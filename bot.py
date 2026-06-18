import asyncio
import logging
import sqlite3
import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove,
    InputMediaPhoto, FSInputFile, BufferedInputFile
)

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

BOT_TOKEN = "8739516166:AAGVEq4oeNb42aY-uDY1vCMOj9mNhsvucmI"

ADMIN_IDS = [7752932648, 8379783147]

# Пароль для входа в админ-панель
ADMIN_PASSWORD = "1329"

DB_PATH = "sonnenrad.db"

SHOP_NAME = "Sönnenrad"

DEFAULT_PAYMENT_LINK = "https://www.tinkoff.ru/rm/r_HbPZNUiqBU.jnNWRPlZwL/vygOe35729"

LOGO_PATH = "sonnenrad_logo.jpg"

# ─────────────────────────────────────────────
# TRANSLATIONS
# ─────────────────────────────────────────────

LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "uk": "🇺🇦 Українська",
    "en": "🇬🇧 English",
    "no": "🇳🇴 Norsk",
    "sv": "🇸🇪 Svenska",
}

T: Dict[str, Dict[str, str]] = {
    "welcome_img": {
        "ru": (
            "☀️ <b>Добро пожаловать в Sönnenrad!</b>\n\n"
            "Мы — языческий магазин северной традиции. "
            "У нас вы найдёте одежду и аксессуары, созданные с духом древних символов:\n\n"
            "👕 Футболки, поло и кофты\n"
            "🧥 Свитшоты и худи\n"
            "🧢 Кепки и головные уборы\n"
            "👜 Сумки и рюкзаки\n"
            "👗 Женская одежда\n"
            "⚡ Мьёльниры, руны, Валькнут и другая атрибутика\n\n"
            "Каждая вещь создана с уважением к культуре предков.\n\n"
            "⚒ Выберите язык, чтобы начать:"
        ),
        "uk": (
            "☀️ <b>Ласкаво просимо до Sönnenrad!</b>\n\n"
            "Ми — язичницький магазин північної традиції. "
            "У нас ви знайдете одяг та аксесуари з духом давніх символів:\n\n"
            "👕 Футболки, поло та кофти\n"
            "🧥 Світшоти та худі\n"
            "🧢 Кепки та головні убори\n"
            "👜 Сумки та рюкзаки\n"
            "👗 Жіночий одяг\n"
            "⚡ Мьйольніри, руни, Валькнут та інша атрибутика\n\n"
            "⚒ Оберіть мову, щоб почати:"
        ),
        "en": (
            "☀️ <b>Welcome to Sönnenrad!</b>\n\n"
            "We are a pagan shop of the Northern Tradition. "
            "Here you'll find clothing and accessories inspired by ancient symbols:\n\n"
            "👕 T-shirts, polo shirts and hoodies\n"
            "🧥 Sweatshirts and pullovers\n"
            "🧢 Caps and headwear\n"
            "👜 Bags and backpacks\n"
            "👗 Women's clothing\n"
            "⚡ Mjölnirs, runes, Valknut and sacred items\n\n"
            "⚒ Choose your language to begin:"
        ),
        "no": (
            "☀️ <b>Velkommen til Sönnenrad!</b>\n\n"
            "Vi er en hedensk butikk i den nordiske tradisjonen. "
            "Her finner du klær og tilbehør inspirert av gamle symboler:\n\n"
            "👕 T-skjorter, poloskjorter og hettegensere\n"
            "🧥 Sweatshirts og gensere\n"
            "🧢 Caps og hodeplagg\n"
            "👜 Vesker og ryggsekker\n"
            "👗 Dameklær\n"
            "⚡ Mjølner, runer, Valknut og hellige gjenstander\n\n"
            "⚒ Velg språk for å begynne:"
        ),
        "sv": (
            "☀️ <b>Välkommen till Sönnenrad!</b>\n\n"
            "Vi är en hednisk butik i den nordiska traditionen. "
            "Här hittar du kläder och accessoarer inspirerade av gamla symboler:\n\n"
            "👕 T-shirts, pikétröjor och hoodies\n"
            "🧥 Sweatshirts och tröjor\n"
            "🧢 Kepsar och huvudbonader\n"
            "👜 Väskor och ryggsäckar\n"
            "👗 Damkläder\n"
            "⚡ Mjölnir, runor, Valknut och heliga föremål\n\n"
            "⚒ Välj språk för att börja:"
        ),
    },
    "maintenance": {
        "ru": (
            "🔧 <b>Магазин временно закрыт на техническое обслуживание.</b>\n\n"
            "{time_info}"
            "Приносим извинения за неудобства. Скоро вернёмся! ☀️"
        ),
        "uk": (
            "🔧 <b>Магазин тимчасово закритий на технічне обслуговування.</b>\n\n"
            "{time_info}"
            "Вибачте за незручності. Незабаром повернемось! ☀️"
        ),
        "en": (
            "🔧 <b>The shop is temporarily closed for maintenance.</b>\n\n"
            "{time_info}"
            "We apologise for the inconvenience. We'll be back soon! ☀️"
        ),
        "no": (
            "🔧 <b>Butikken er midlertidig stengt for vedlikehold.</b>\n\n"
            "{time_info}"
            "Vi beklager ulempen. Vi er snart tilbake! ☀️"
        ),
        "sv": (
            "🔧 <b>Butiken är tillfälligt stängd för underhåll.</b>\n\n"
            "{time_info}"
            "Vi ber om ursäkt för besväret. Vi är snart tillbaka! ☀️"
        ),
    },
    "maintenance_time": {
        "ru": "⏱ Примерное время: <b>{time}</b>\n\n",
        "uk": "⏱ Приблизний час: <b>{time}</b>\n\n",
        "en": "⏱ Estimated time: <b>{time}</b>\n\n",
        "no": "⏱ Estimert tid: <b>{time}</b>\n\n",
        "sv": "⏱ Beräknad tid: <b>{time}</b>\n\n",
    },
    "welcome": {
        "ru": f"☀️ Добро пожаловать в <b>{SHOP_NAME}</b>!\n\nВыберите язык:",
        "uk": f"☀️ Ласкаво просимо до <b>{SHOP_NAME}</b>!\n\nОберіть мову:",
        "en": f"☀️ Welcome to <b>{SHOP_NAME}</b>!\n\nChoose your language:",
        "no": f"☀️ Velkommen til <b>{SHOP_NAME}</b>!\n\nVelg språk:",
        "sv": f"☀️ Välkommen till <b>{SHOP_NAME}</b>!\n\nVälj språk:",
    },
    "language_saved": {
        "ru": "✅ Язык сохранён. Добро пожаловать!",
        "uk": "✅ Мову збережено. Ласкаво просимо!",
        "en": "✅ Language saved. Welcome!",
        "no": "✅ Språk lagret. Velkommen!",
        "sv": "✅ Språk sparat. Välkommen!",
    },
    "main_menu": {
        "ru": "🏠 <b>Главное меню</b>\n\nВыберите раздел:",
        "uk": "🏠 <b>Головне меню</b>\n\nОберіть розділ:",
        "en": "🏠 <b>Main Menu</b>\n\nChoose a section:",
        "no": "🏠 <b>Hovedmeny</b>\n\nVelg en seksjon:",
        "sv": "🏠 <b>Huvudmeny</b>\n\nVälj en sektion:",
    },
    "catalog": {
        "ru": "🛍 Каталог",
        "uk": "🛍 Каталог",
        "en": "🛍 Catalog",
        "no": "🛍 Katalog",
        "sv": "🛍 Katalog",
    },
    "cart": {
        "ru": "🛒 Корзина",
        "uk": "🛒 Кошик",
        "en": "🛒 Cart",
        "no": "🛒 Handlekurv",
        "sv": "🛒 Varukorg",
    },
    "my_orders": {
        "ru": "📦 Мои заказы",
        "uk": "📦 Мої замовлення",
        "en": "📦 My Orders",
        "no": "📦 Mine bestillinger",
        "sv": "📦 Mina beställningar",
    },
    "settings": {
        "ru": "⚙️ Настройки",
        "uk": "⚙️ Налаштування",
        "en": "⚙️ Settings",
        "no": "⚙️ Innstillinger",
        "sv": "⚙️ Inställningar",
    },
    "change_language": {
        "ru": "🌐 Сменить язык",
        "uk": "🌐 Змінити мову",
        "en": "🌐 Change Language",
        "no": "🌐 Bytt språk",
        "sv": "🌐 Byt språk",
    },
    "choose_category": {
        "ru": "🗂 Выберите категорию:",
        "uk": "🗂 Оберіть категорію:",
        "en": "🗂 Choose a category:",
        "no": "🗂 Velg en kategori:",
        "sv": "🗂 Välj en kategori:",
    },
    "catalog_empty": {
        "ru": "😔 В этой категории пока нет товаров.",
        "uk": "😔 У цій категорії поки немає товарів.",
        "en": "😔 No items in this category yet.",
        "no": "😔 Ingen varer i denne kategorien ennå.",
        "sv": "😔 Inga varor i den här kategorin ännu.",
    },
    "no_categories": {
        "ru": "😔 Каталог пуст. Загляните позже!",
        "uk": "😔 Каталог порожній. Зайдіть пізніше!",
        "en": "😔 Catalog is empty. Check back later!",
        "no": "😔 Katalogen er tom. Sjekk tilbake senere!",
        "sv": "😔 Katalogen är tom. Kom tillbaka senare!",
    },
    "select_size": {
        "ru": "📐 Выберите размер:",
        "uk": "📐 Оберіть розмір:",
        "en": "📐 Select size:",
        "no": "📐 Velg størrelse:",
        "sv": "📐 Välj storlek:",
    },
    "select_color": {
        "ru": "🎨 Выберите цвет:",
        "uk": "🎨 Оберіть колір:",
        "en": "🎨 Select color:",
        "no": "🎨 Velg farge:",
        "sv": "🎨 Välj färg:",
    },
    "added_to_cart": {
        "ru": "✅ Товар добавлен в корзину!\n\nЧто дальше?",
        "uk": "✅ Товар додано до кошика!\n\nЩо далі?",
        "en": "✅ Item added to cart!\n\nWhat's next?",
        "no": "✅ Vare lagt til i handlekurven!\n\nHva nå?",
        "sv": "✅ Vara tillagd i varukorgen!\n\nVad händer nu?",
    },
    "cart_empty": {
        "ru": "🛒 Ваша корзина пуста.\n\nДобавьте товары из каталога!",
        "uk": "🛒 Ваш кошик порожній.\n\nДодайте товари з каталогу!",
        "en": "🛒 Your cart is empty.\n\nAdd items from the catalog!",
        "no": "🛒 Handlekurven er tom.\n\nLegg til varer fra katalogen!",
        "sv": "🛒 Varukorgen är tom.\n\nLägg till varor från katalogen!",
    },
    "cart_header": {
        "ru": "🛒 <b>Ваша корзина:</b>",
        "uk": "🛒 <b>Ваш кошик:</b>",
        "en": "🛒 <b>Your Cart:</b>",
        "no": "🛒 <b>Din handlekurv:</b>",
        "sv": "🛒 <b>Din varukorg:</b>",
    },
    "cart_total": {
        "ru": "\n💰 <b>Итого: {total} ₽</b>",
        "uk": "\n💰 <b>Разом: {total} ₽</b>",
        "en": "\n💰 <b>Total: {total} ₽</b>",
        "no": "\n💰 <b>Totalt: {total} ₽</b>",
        "sv": "\n💰 <b>Totalt: {total} ₽</b>",
    },
    "checkout": {
        "ru": "✅ Оформить заказ",
        "uk": "✅ Оформити замовлення",
        "en": "✅ Checkout",
        "no": "✅ Gå til kassen",
        "sv": "✅ Gå till kassan",
    },
    "clear_cart": {
        "ru": "🗑 Очистить корзину",
        "uk": "🗑 Очистити кошик",
        "en": "🗑 Clear Cart",
        "no": "🗑 Tøm handlekurv",
        "sv": "🗑 Töm varukorgen",
    },
    "cart_cleared": {
        "ru": "🗑 Корзина очищена.",
        "uk": "🗑 Кошик очищено.",
        "en": "🗑 Cart cleared.",
        "no": "🗑 Handlekurven er tømt.",
        "sv": "🗑 Varukorgen är tömd.",
    },
    "enter_name": {
        "ru": "👤 <b>Шаг 1 из 4</b>\n\nВведите ваше <b>имя и фамилию</b>:",
        "uk": "👤 <b>Крок 1 з 4</b>\n\nВведіть ваше <b>ім'я та прізвище</b>:",
        "en": "👤 <b>Step 1 of 4</b>\n\nEnter your <b>full name</b>:",
        "no": "👤 <b>Trinn 1 av 4</b>\n\nSkriv inn ditt <b>fulle navn</b>:",
        "sv": "👤 <b>Steg 1 av 4</b>\n\nAnge ditt <b>fullständiga namn</b>:",
    },
    "enter_phone": {
        "ru": "📱 <b>Шаг 2 из 4</b>\n\nВведите ваш <b>номер телефона</b>:\n\n<i>Пример: +7 999 123 45 67</i>",
        "uk": "📱 <b>Крок 2 з 4</b>\n\nВведіть ваш <b>номер телефону</b>:\n\n<i>Приклад: +38 099 123 45 67</i>",
        "en": "📱 <b>Step 2 of 4</b>\n\nEnter your <b>phone number</b>:\n\n<i>Example: +1 555 123 4567</i>",
        "no": "📱 <b>Trinn 2 av 4</b>\n\nSkriv inn ditt <b>telefonnummer</b>:",
        "sv": "📱 <b>Steg 2 av 4</b>\n\nAnge ditt <b>telefonnummer</b>:",
    },
    "enter_address": {
        "ru": "📍 <b>Шаг 3 из 4</b>\n\nВведите <b>адрес доставки</b>:\n\n<i>Пример: г. Москва, ул. Ленина 1, кв. 5</i>",
        "uk": "📍 <b>Крок 3 з 4</b>\n\nВведіть <b>адресу доставки</b>:\n\n<i>Приклад: м. Київ, вул. Хрещатик 1, кв. 5</i>",
        "en": "📍 <b>Step 3 of 4</b>\n\nEnter your <b>delivery address</b>:\n\n<i>Example: 123 Main St, New York, NY 10001</i>",
        "no": "📍 <b>Trinn 3 av 4</b>\n\nSkriv inn <b>leveringsadressen</b>:",
        "sv": "📍 <b>Steg 3 av 4</b>\n\nAnge <b>leveransadressen</b>:",
    },
    "enter_promo": {
        "ru": "🎟 <b>Шаг 4 из 4</b>\n\nЕсть промокод? Введите его или нажмите «Пропустить»:",
        "uk": "🎟 <b>Крок 4 з 4</b>\n\nМаєте промокод? Введіть його або натисніть «Пропустити»:",
        "en": "🎟 <b>Step 4 of 4</b>\n\nHave a promo code? Enter it or press 'Skip':",
        "no": "🎟 <b>Trinn 4 av 4</b>\n\nHar du en kampanjekode? Skriv den inn eller trykk 'Hopp over':",
        "sv": "🎟 <b>Steg 4 av 4</b>\n\nHar du en kampanjkod? Ange den eller tryck 'Hoppa över':",
    },
    "skip": {
        "ru": "⏩ Пропустить",
        "uk": "⏩ Пропустити",
        "en": "⏩ Skip",
        "no": "⏩ Hopp over",
        "sv": "⏩ Hoppa över",
    },
    "promo_applied": {
        "ru": "✅ Промокод применён! Скидка: <b>{discount}</b>",
        "uk": "✅ Промокод застосовано! Знижка: <b>{discount}</b>",
        "en": "✅ Promo code applied! Discount: <b>{discount}</b>",
        "no": "✅ Kampanjekode brukt! Rabatt: <b>{discount}</b>",
        "sv": "✅ Kampanjkod tillämpad! Rabatt: <b>{discount}</b>",
    },
    "promo_invalid": {
        "ru": "❌ Неверный или неактивный промокод. Попробуйте ещё раз или нажмите «Пропустить»:",
        "uk": "❌ Невірний або неактивний промокод. Спробуйте ще раз або натисніть «Пропустити»:",
        "en": "❌ Invalid or inactive promo code. Try again or press 'Skip':",
        "no": "❌ Ugyldig eller inaktiv kampanjekode. Prøv igjen eller trykk 'Hopp over':",
        "sv": "❌ Ogiltig eller inaktiv kampanjkod. Försök igen eller tryck 'Hoppa över':",
    },
    "order_confirm": {
        "ru": (
            "📋 <b>Проверьте ваш заказ:</b>\n\n"
            "{items}\n\n"
            "👤 Имя: <b>{name}</b>\n"
            "📱 Телефон: <b>{phone}</b>\n"
            "📍 Адрес: <b>{address}</b>\n"
            "{promo_line}"
            "💰 Итого: <b>{total} ₽</b>\n\n"
            "Всё верно?"
        ),
        "uk": (
            "📋 <b>Перевірте ваше замовлення:</b>\n\n"
            "{items}\n\n"
            "👤 Ім'я: <b>{name}</b>\n"
            "📱 Телефон: <b>{phone}</b>\n"
            "📍 Адреса: <b>{address}</b>\n"
            "{promo_line}"
            "💰 Разом: <b>{total} ₽</b>\n\n"
            "Все вірно?"
        ),
        "en": (
            "📋 <b>Review your order:</b>\n\n"
            "{items}\n\n"
            "👤 Name: <b>{name}</b>\n"
            "📱 Phone: <b>{phone}</b>\n"
            "📍 Address: <b>{address}</b>\n"
            "{promo_line}"
            "💰 Total: <b>{total} ₽</b>\n\n"
            "Everything correct?"
        ),
        "no": (
            "📋 <b>Se gjennom bestillingen din:</b>\n\n"
            "{items}\n\n"
            "👤 Navn: <b>{name}</b>\n"
            "📱 Telefon: <b>{phone}</b>\n"
            "📍 Adresse: <b>{address}</b>\n"
            "{promo_line}"
            "💰 Totalt: <b>{total} ₽</b>\n\n"
            "Er alt riktig?"
        ),
        "sv": (
            "📋 <b>Granska din beställning:</b>\n\n"
            "{items}\n\n"
            "👤 Namn: <b>{name}</b>\n"
            "📱 Telefon: <b>{phone}</b>\n"
            "📍 Adress: <b>{address}</b>\n"
            "{promo_line}"
            "💰 Totalt: <b>{total} ₽</b>\n\n"
            "Stämmer allt?"
        ),
    },
    "confirm": {
        "ru": "✅ Подтвердить",
        "uk": "✅ Підтвердити",
        "en": "✅ Confirm",
        "no": "✅ Bekreft",
        "sv": "✅ Bekräfta",
    },
    "cancel": {
        "ru": "❌ Отмена",
        "uk": "❌ Скасувати",
        "en": "❌ Cancel",
        "no": "❌ Avbryt",
        "sv": "❌ Avbryt",
    },
    "order_placed": {
        "ru": (
            "🎉 <b>Заказ #{order_id} оформлен!</b>\n\n"
            "💳 <b>Как оплатить:</b>\n"
            "1️⃣ Нажмите кнопку <b>«Оплатить»</b> ниже\n"
            "2️⃣ Перейдите на страницу оплаты и оплатите заказ\n"
            "3️⃣ Вернитесь сюда и нажмите <b>«✅ Я оплатил»</b>\n"
            "4️⃣ Ожидайте подтверждения от администратора\n\n"
            "<i>⚠️ Не закрывайте чат до нажатия «Я оплатил»!</i>"
        ),
        "uk": (
            "🎉 <b>Замовлення #{order_id} оформлено!</b>\n\n"
            "💳 <b>Як оплатити:</b>\n"
            "1️⃣ Натисніть кнопку <b>«Оплатити»</b> нижче\n"
            "2️⃣ Перейдіть на сторінку оплати та сплатіть замовлення\n"
            "3️⃣ Поверніться сюди та натисніть <b>«✅ Я оплатив»</b>\n"
            "4️⃣ Очікуйте підтвердження від адміністратора\n\n"
            "<i>⚠️ Не закривайте чат до натискання «Я оплатив»!</i>"
        ),
        "en": (
            "🎉 <b>Order #{order_id} placed!</b>\n\n"
            "💳 <b>How to pay:</b>\n"
            "1️⃣ Click the <b>«Pay»</b> button below\n"
            "2️⃣ Complete payment on the payment page\n"
            "3️⃣ Return here and press <b>«✅ I've paid»</b>\n"
            "4️⃣ Wait for confirmation from the administrator\n\n"
            "<i>⚠️ Don't close the chat before pressing «I've paid»!</i>"
        ),
        "no": (
            "🎉 <b>Bestilling #{order_id} er lagt inn!</b>\n\n"
            "💳 <b>Slik betaler du:</b>\n"
            "1️⃣ Klikk på <b>«Betal»</b>-knappen nedenfor\n"
            "2️⃣ Fullfør betalingen på betalingssiden\n"
            "3️⃣ Kom tilbake hit og trykk <b>«✅ Jeg har betalt»</b>\n"
            "4️⃣ Vent på bekreftelse fra administrator\n\n"
            "<i>⚠️ Ikke lukk chatten før du trykker «Jeg har betalt»!</i>"
        ),
        "sv": (
            "🎉 <b>Beställning #{order_id} lagd!</b>\n\n"
            "💳 <b>Så här betalar du:</b>\n"
            "1️⃣ Klicka på knappen <b>«Betala»</b> nedan\n"
            "2️⃣ Slutför betalningen på betalningssidan\n"
            "3️⃣ Kom tillbaka hit och tryck <b>«✅ Jag har betalat»</b>\n"
            "4️⃣ Vänta på bekräftelse från administratören\n\n"
            "<i>⚠️ Stäng inte chatten innan du tryckt «Jag har betalat»!</i>"
        ),
    },
    "pay_button": {
        "ru": "💳 Оплатить",
        "uk": "💳 Оплатити",
        "en": "💳 Pay",
        "no": "💳 Betal",
        "sv": "💳 Betala",
    },
    "paid_button": {
        "ru": "✅ Я оплатил",
        "uk": "✅ Я оплатив",
        "en": "✅ I've paid",
        "no": "✅ Jeg har betalt",
        "sv": "✅ Jag har betalat",
    },
    "paid_confirm_msg": {
        "ru": "⏳ <b>Заявка отправлена!</b>\n\nАдминистратор проверит оплату и подтвердит заказ. Обычно это занимает до 30 минут.",
        "uk": "⏳ <b>Заявку відправлено!</b>\n\nАдміністратор перевірить оплату та підтвердить замовлення. Зазвичай це займає до 30 хвилин.",
        "en": "⏳ <b>Request sent!</b>\n\nThe administrator will verify your payment and confirm the order. This usually takes up to 30 minutes.",
        "no": "⏳ <b>Forespørsel sendt!</b>\n\nAdministratoren vil bekrefte betalingen og ordren. Dette tar vanligvis opptil 30 minutter.",
        "sv": "⏳ <b>Förfrågan skickad!</b>\n\nAdministratören bekräftar betalningen och beställningen. Det brukar ta upp till 30 minuter.",
    },
    "order_approved": {
        "ru": "✅ <b>Заказ #{order_id} подтверждён!</b>\n\nСпасибо за покупку в {shop}! Ваш заказ передан в обработку. 🎉",
        "uk": "✅ <b>Замовлення #{order_id} підтверджено!</b>\n\nДякуємо за покупку в {shop}! Ваше замовлення передано в обробку. 🎉",
        "en": "✅ <b>Order #{order_id} confirmed!</b>\n\nThank you for shopping at {shop}! Your order is being processed. 🎉",
        "no": "✅ <b>Bestilling #{order_id} bekreftet!</b>\n\nTakk for at du handlet hos {shop}! Bestillingen din behandles nå. 🎉",
        "sv": "✅ <b>Beställning #{order_id} bekräftad!</b>\n\nTack för att du handlade hos {shop}! Din beställning behandlas nu. 🎉",
    },
    "order_rejected": {
        "ru": "❌ <b>Заказ #{order_id} отклонён.</b>\n\nПожалуйста, свяжитесь с поддержкой для уточнения деталей.",
        "uk": "❌ <b>Замовлення #{order_id} відхилено.</b>\n\nБудь ласка, зверніться до підтримки для уточнення деталей.",
        "en": "❌ <b>Order #{order_id} rejected.</b>\n\nPlease contact support for more details.",
        "no": "❌ <b>Bestilling #{order_id} ble avvist.</b>\n\nVennligst kontakt støtte for mer informasjon.",
        "sv": "❌ <b>Beställning #{order_id} avvisad.</b>\n\nKontakta support för mer information.",
    },
    "no_orders": {
        "ru": "📦 У вас пока нет заказов.\n\nСделайте первый заказ в каталоге! 🛍",
        "uk": "📦 У вас поки немає замовлень.\n\nЗробіть перше замовлення в каталозі! 🛍",
        "en": "📦 You have no orders yet.\n\nMake your first order from the catalog! 🛍",
        "no": "📦 Du har ingen bestillinger ennå.\n\nLegg inn din første bestilling fra katalogen! 🛍",
        "sv": "📦 Du har inga beställningar ännu.\n\nGör din första beställning från katalogen! 🛍",
    },
    "order_status_pending": {
        "ru": "⏳ Ожидает оплаты",
        "uk": "⏳ Очікує оплати",
        "en": "⏳ Pending Payment",
        "no": "⏳ Venter på betaling",
        "sv": "⏳ Väntar på betalning",
    },
    "order_status_paid": {
        "ru": "💳 Оплачен, ожидает подтверждения",
        "uk": "💳 Оплачено, очікує підтвердження",
        "en": "💳 Paid, awaiting confirmation",
        "no": "💳 Betalt, venter på bekreftelse",
        "sv": "💳 Betald, väntar på bekräftelse",
    },
    "order_status_confirmed": {
        "ru": "✅ Подтверждён",
        "uk": "✅ Підтверджено",
        "en": "✅ Confirmed",
        "no": "✅ Bekreftet",
        "sv": "✅ Bekräftad",
    },
    "order_status_rejected": {
        "ru": "❌ Отклонён",
        "uk": "❌ Відхилено",
        "en": "❌ Rejected",
        "no": "❌ Avvist",
        "sv": "❌ Avvisad",
    },
    "back": {
        "ru": "⬅️ Назад",
        "uk": "⬅️ Назад",
        "en": "⬅️ Back",
        "no": "⬅️ Tilbake",
        "sv": "⬅️ Tillbaka",
    },
    "add_to_cart": {
        "ru": "🛒 В корзину",
        "uk": "🛒 До кошика",
        "en": "🛒 Add to Cart",
        "no": "🛒 Legg i handlekurv",
        "sv": "🛒 Lägg i varukorg",
    },
    "back_to_catalog": {
        "ru": "📋 К категориям",
        "uk": "📋 До категорій",
        "en": "📋 Back to Catalog",
        "no": "📋 Tilbake til katalog",
        "sv": "📋 Tillbaka till katalog",
    },
    "out_of_stock": {
        "ru": "❌ Нет в наличии",
        "uk": "❌ Немає в наявності",
        "en": "❌ Out of Stock",
        "no": "❌ Ikke på lager",
        "sv": "❌ Slut i lager",
    },
    "go_to_cart": {
        "ru": "🛒 Перейти в корзину",
        "uk": "🛒 Перейти до кошика",
        "en": "🛒 Go to Cart",
        "no": "🛒 Gå til handlekurv",
        "sv": "🛒 Gå till varukorgen",
    },
    "continue_shopping": {
        "ru": "🛍 Продолжить покупки",
        "uk": "🛍 Продовжити покупки",
        "en": "🛍 Continue Shopping",
        "no": "🛍 Fortsett å handle",
        "sv": "🛍 Fortsätt handla",
    },
    "promo_label": {
        "ru": "🎟 Промокод: {code} (-{discount})\n",
        "uk": "🎟 Промокод: {code} (-{discount})\n",
        "en": "🎟 Promo: {code} (-{discount})\n",
        "no": "🎟 Kampanje: {code} (-{discount})\n",
        "sv": "🎟 Kampanj: {code} (-{discount})\n",
    },
    "banned_message": {
        "ru": "🚫 <b>Ваш аккаунт заблокирован.</b>\n\nОбратитесь в поддержку.",
        "uk": "🚫 <b>Ваш акаунт заблокований.</b>\n\nЗверніться до підтримки.",
        "en": "🚫 <b>Your account is banned.</b>\n\nPlease contact support.",
        "no": "🚫 <b>Kontoen din er utestengt.</b>\n\nKontakt support.",
        "sv": "🚫 <b>Ditt konto är blockerat.</b>\n\nKontakta support.",
    },
}


def t(key: str, lang: str, **kwargs) -> str:
    text = T.get(key, {}).get(lang) or T.get(key, {}).get("en", key)
    for k, v in kwargs.items():
        text = text.replace("{" + k + "}", str(v))
    return text


# ─────────────────────────────────────────────
# DATABASE
# ─────────────────────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    c = conn.cursor()

    c.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        tg_id INTEGER UNIQUE NOT NULL,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        lang TEXT DEFAULT 'en',
        is_banned INTEGER DEFAULT 0,
        note TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        emoji TEXT DEFAULT '👗',
        sort_order INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        old_price REAL,
        photos TEXT DEFAULT '[]',
        sizes TEXT DEFAULT '[]',
        colors TEXT DEFAULT '[]',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS product_stock (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        product_id INTEGER NOT NULL,
        size TEXT NOT NULL,
        color TEXT NOT NULL,
        stock INTEGER DEFAULT 0,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
        UNIQUE(product_id, size, color)
    );

    CREATE TABLE IF NOT EXISTS cart (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        size TEXT NOT NULL,
        color TEXT NOT NULL,
        quantity INTEGER DEFAULT 1,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tg_id INTEGER NOT NULL,
        name TEXT NOT NULL,
        phone TEXT NOT NULL,
        address TEXT NOT NULL,
        items TEXT NOT NULL,
        promo_code TEXT,
        discount_amount REAL DEFAULT 0,
        total REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS promo_codes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        code TEXT UNIQUE NOT NULL,
        type TEXT NOT NULL,
        value REAL NOT NULL,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    );
    """)

    # Добавляем колонки если их нет (для существующих БД)
    try:
        c.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
    except Exception:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN note TEXT DEFAULT ''")
    except Exception:
        pass

    c.execute(
        "INSERT OR IGNORE INTO settings (key, value) VALUES ('payment_link', ?)",
        (DEFAULT_PAYMENT_LINK,)
    )
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('maintenance', '0')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('maintenance_time', '')")
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# DB HELPERS
# ─────────────────────────────────────────────

def db_get_user(tg_id: int) -> Optional[sqlite3.Row]:
    conn = get_db()
    row = conn.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)).fetchone()
    conn.close()
    return row


def db_upsert_user(tg_id: int, username: str, first_name: str, last_name: str, lang: str = "en"):
    conn = get_db()
    conn.execute("""
        INSERT INTO users (tg_id, username, first_name, last_name, lang)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(tg_id) DO UPDATE SET username=excluded.username,
            first_name=excluded.first_name, last_name=excluded.last_name
    """, (tg_id, username, first_name, last_name, lang))
    conn.commit()
    conn.close()


def db_set_lang(tg_id: int, lang: str):
    conn = get_db()
    conn.execute("UPDATE users SET lang=? WHERE tg_id=?", (lang, tg_id))
    conn.commit()
    conn.close()


def db_get_lang(tg_id: int) -> str:
    user = db_get_user(tg_id)
    return user["lang"] if user else "en"


def db_is_banned(tg_id: int) -> bool:
    user = db_get_user(tg_id)
    return bool(user and user["is_banned"])


def db_ban_user(tg_id: int):
    conn = get_db()
    conn.execute("UPDATE users SET is_banned=1 WHERE tg_id=?", (tg_id,))
    conn.commit()
    conn.close()


def db_unban_user(tg_id: int):
    conn = get_db()
    conn.execute("UPDATE users SET is_banned=0 WHERE tg_id=?", (tg_id,))
    conn.commit()
    conn.close()


def db_set_user_note(tg_id: int, note: str):
    conn = get_db()
    conn.execute("UPDATE users SET note=? WHERE tg_id=?", (note, tg_id))
    conn.commit()
    conn.close()


def db_is_maintenance() -> bool:
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key='maintenance'").fetchone()
    conn.close()
    return row and row["value"] == "1"


def db_get_maintenance_time() -> str:
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key='maintenance_time'").fetchone()
    conn.close()
    return row["value"] if row else ""


# ── CATEGORIES ──

def db_get_active_categories():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM categories WHERE is_active=1 ORDER BY sort_order, id"
    ).fetchall()
    conn.close()
    return rows


def db_get_all_categories():
    conn = get_db()
    rows = conn.execute("SELECT * FROM categories ORDER BY sort_order, id").fetchall()
    conn.close()
    return rows


def db_get_category(cat_id: int) -> Optional[sqlite3.Row]:
    conn = get_db()
    row = conn.execute("SELECT * FROM categories WHERE id=?", (cat_id,)).fetchone()
    conn.close()
    return row


def db_add_category(name: str, emoji: str, sort_order: int = 0) -> int:
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO categories (name, emoji, sort_order) VALUES (?,?,?)",
        (name, emoji, sort_order)
    )
    cat_id = cur.lastrowid
    conn.commit()
    conn.close()
    return cat_id


def db_update_category(cat_id: int, name: str, emoji: str, sort_order: int, is_active: int):
    conn = get_db()
    conn.execute(
        "UPDATE categories SET name=?, emoji=?, sort_order=?, is_active=? WHERE id=?",
        (name, emoji, sort_order, is_active, cat_id)
    )
    conn.commit()
    conn.close()


def db_delete_category(cat_id: int):
    conn = get_db()
    conn.execute("DELETE FROM categories WHERE id=?", (cat_id,))
    conn.commit()
    conn.close()


# ── PRODUCTS ──

def db_get_products_by_category(cat_id: int):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM products WHERE category_id=? AND is_active=1 ORDER BY id DESC",
        (cat_id,)
    ).fetchall()
    conn.close()
    return rows


def db_get_product(product_id: int) -> Optional[sqlite3.Row]:
    conn = get_db()
    row = conn.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
    conn.close()
    return row


def db_get_stock(product_id: int, size: str, color: str) -> int:
    conn = get_db()
    row = conn.execute(
        "SELECT stock FROM product_stock WHERE product_id=? AND size=? AND color=?",
        (product_id, size, color)
    ).fetchone()
    conn.close()
    return row["stock"] if row else 0


def db_get_all_stock(product_id: int):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM product_stock WHERE product_id=?", (product_id,)
    ).fetchall()
    conn.close()
    return rows


def db_set_stock(product_id: int, size: str, color: str, stock: int):
    conn = get_db()
    conn.execute("""
        INSERT INTO product_stock (product_id, size, color, stock)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(product_id, size, color) DO UPDATE SET stock=excluded.stock
    """, (product_id, size, color, stock))
    conn.commit()
    conn.close()


def db_decrement_stock(product_id: int, size: str, color: str, qty: int) -> int:
    conn = get_db()
    row = conn.execute(
        "SELECT stock FROM product_stock WHERE product_id=? AND size=? AND color=?",
        (product_id, size, color)
    ).fetchone()
    new_stock = max(0, (row["stock"] if row else 0) - qty)
    conn.execute("""
        INSERT INTO product_stock (product_id, size, color, stock)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(product_id, size, color) DO UPDATE SET stock=excluded.stock
    """, (product_id, size, color, new_stock))
    conn.commit()
    conn.close()
    return new_stock


def db_get_cart(tg_id: int):
    conn = get_db()
    rows = conn.execute("""
        SELECT c.*, p.name, p.price FROM cart c
        JOIN products p ON c.product_id=p.id
        WHERE c.tg_id=?
    """, (tg_id,)).fetchall()
    conn.close()
    return rows


def db_add_to_cart(tg_id: int, product_id: int, size: str, color: str):
    conn = get_db()
    existing = conn.execute(
        "SELECT id, quantity FROM cart WHERE tg_id=? AND product_id=? AND size=? AND color=?",
        (tg_id, product_id, size, color)
    ).fetchone()
    if existing:
        conn.execute("UPDATE cart SET quantity=quantity+1 WHERE id=?", (existing["id"],))
    else:
        conn.execute(
            "INSERT INTO cart (tg_id, product_id, size, color, quantity) VALUES (?,?,?,?,1)",
            (tg_id, product_id, size, color)
        )
    conn.commit()
    conn.close()


def db_remove_from_cart(cart_id: int):
    conn = get_db()
    conn.execute("DELETE FROM cart WHERE id=?", (cart_id,))
    conn.commit()
    conn.close()


def db_update_cart_qty(cart_id: int, qty: int):
    conn = get_db()
    if qty <= 0:
        conn.execute("DELETE FROM cart WHERE id=?", (cart_id,))
    else:
        conn.execute("UPDATE cart SET quantity=? WHERE id=?", (qty, cart_id))
    conn.commit()
    conn.close()


def db_clear_cart(tg_id: int):
    conn = get_db()
    conn.execute("DELETE FROM cart WHERE tg_id=?", (tg_id,))
    conn.commit()
    conn.close()


def db_get_promo(code: str) -> Optional[sqlite3.Row]:
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM promo_codes WHERE code=? AND is_active=1",
        (code.upper(),)
    ).fetchone()
    conn.close()
    return row


def db_create_order(tg_id: int, name: str, phone: str, address: str, items: list,
                    promo_code: str, discount_amount: float, total: float) -> int:
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO orders (tg_id, name, phone, address, items, promo_code, discount_amount, total)
        VALUES (?,?,?,?,?,?,?,?)
    """, (tg_id, name, phone, address, json.dumps(items, ensure_ascii=False),
          promo_code, discount_amount, total))
    order_id = cur.lastrowid
    conn.commit()
    conn.close()
    return order_id


def db_get_order(order_id: int) -> Optional[sqlite3.Row]:
    conn = get_db()
    row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    conn.close()
    return row


def db_set_order_status(order_id: int, status: str):
    conn = get_db()
    conn.execute("UPDATE orders SET status=? WHERE id=?", (status, order_id))
    conn.commit()
    conn.close()


def db_get_user_orders(tg_id: int):
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM orders WHERE tg_id=? ORDER BY id DESC", (tg_id,)
    ).fetchall()
    conn.close()
    return rows


def db_get_setting(key: str) -> str:
    conn = get_db()
    row = conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
    conn.close()
    return row["value"] if row else ""


def db_set_setting(key: str, value: str):
    conn = get_db()
    conn.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()


def db_get_all_users():
    conn = get_db()
    rows = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    conn.close()
    return rows


def db_get_all_orders():
    conn = get_db()
    rows = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()
    return rows


def db_get_all_products():
    conn = get_db()
    rows = conn.execute("""
        SELECT p.*, c.name as cat_name FROM products p
        LEFT JOIN categories c ON p.category_id=c.id
        ORDER BY p.id DESC
    """).fetchall()
    conn.close()
    return rows


def db_get_all_promos():
    conn = get_db()
    rows = conn.execute("SELECT * FROM promo_codes ORDER BY id DESC").fetchall()
    conn.close()
    return rows


def db_add_product(name, description, price, old_price, photos, sizes, colors, category_id=None):
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO products (name, description, price, old_price, photos, sizes, colors, category_id)
        VALUES (?,?,?,?,?,?,?,?)
    """, (name, description, price, old_price,
          json.dumps(photos), json.dumps(sizes), json.dumps(colors), category_id))
    product_id = cur.lastrowid
    conn.commit()
    conn.close()
    return product_id


def db_update_product_field(product_id: int, field: str, value):
    allowed = {"name", "description", "price", "old_price", "photos", "sizes", "colors",
               "is_active", "category_id"}
    if field not in allowed:
        return
    conn = get_db()
    if isinstance(value, (list, dict)):
        value = json.dumps(value, ensure_ascii=False)
    conn.execute(f"UPDATE products SET {field}=? WHERE id=?", (value, product_id))
    conn.commit()
    conn.close()


def db_delete_product(product_id: int):
    conn = get_db()
    conn.execute("DELETE FROM products WHERE id=?", (product_id,))
    conn.commit()
    conn.close()


def db_add_promo(code: str, ptype: str, value: float):
    conn = get_db()
    conn.execute(
        "INSERT INTO promo_codes (code, type, value) VALUES (?,?,?)",
        (code.upper(), ptype, value)
    )
    conn.commit()
    conn.close()


def db_delete_promo(promo_id: int):
    conn = get_db()
    conn.execute("DELETE FROM promo_codes WHERE id=?", (promo_id,))
    conn.commit()
    conn.close()


def db_toggle_promo(promo_id: int):
    conn = get_db()
    conn.execute("UPDATE promo_codes SET is_active = 1-is_active WHERE id=?", (promo_id,))
    conn.commit()
    conn.close()


def db_stats():
    conn = get_db()
    users_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    orders_count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    revenue = conn.execute(
        "SELECT COALESCE(SUM(total),0) FROM orders WHERE status IN ('paid','confirmed')"
    ).fetchone()[0]
    pending_count = conn.execute(
        "SELECT COUNT(*) FROM orders WHERE status='paid'"
    ).fetchone()[0]
    today_orders = conn.execute(
        "SELECT COUNT(*) FROM orders WHERE date(created_at)=date('now')"
    ).fetchone()[0]
    products_count = conn.execute("SELECT COUNT(*) FROM products WHERE is_active=1").fetchone()[0]
    banned_count = conn.execute("SELECT COUNT(*) FROM users WHERE is_banned=1").fetchone()[0]
    new_users_week = conn.execute(
        "SELECT COUNT(*) FROM users WHERE created_at >= datetime('now', '-7 days')"
    ).fetchone()[0]
    conn.close()
    return users_count, orders_count, revenue, pending_count, today_orders, products_count, banned_count, new_users_week


# ─────────────────────────────────────────────
# STATES
# ─────────────────────────────────────────────

class LangState(StatesGroup):
    choosing = State()


class ProductState(StatesGroup):
    selecting_size = State()
    selecting_color = State()


class CheckoutState(StatesGroup):
    name = State()
    phone = State()
    address = State()
    promo = State()
    confirm = State()


# ── Быстрое добавление товара (один блок текста) ──
class AdminQuickAddProduct(StatesGroup):
    category = State()      # выбор категории кнопкой
    text_data = State()     # весь текст одним сообщением
    photos = State()        # фото
    stock = State()         # остатки


class AdminEditProduct(StatesGroup):
    choosing_field = State()
    entering_value = State()
    entering_stock = State()
    entering_photos = State()


class AdminAddPromo(StatesGroup):
    code = State()
    ptype = State()
    value = State()


class AdminBroadcast(StatesGroup):
    message = State()
    confirm = State()


class AdminSetPayLink(StatesGroup):
    link = State()


class AdminAddCategory(StatesGroup):
    name = State()
    emoji = State()
    sort_order = State()


class AdminEditCategory(StatesGroup):
    field = State()
    value = State()


class AdminMaintenance(StatesGroup):
    set_time = State()
    broadcast_confirm = State()


class AdminPasswordState(StatesGroup):
    waiting = State()


class AdminUserAction(StatesGroup):
    waiting_note = State()
    waiting_search = State()
    waiting_message = State()


# ─────────────────────────────────────────────
# KEYBOARDS
# ─────────────────────────────────────────────

def kb_lang_select() -> InlineKeyboardMarkup:
    buttons = [[InlineKeyboardButton(text=name, callback_data=f"lang:{code}")]
               for code, name in LANGUAGES.items()]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def kb_main_menu(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=t("catalog", lang)), KeyboardButton(text=t("cart", lang))],
            [KeyboardButton(text=t("my_orders", lang)), KeyboardButton(text=t("settings", lang))],
        ],
        resize_keyboard=True
    )


def kb_categories(categories, lang: str) -> InlineKeyboardMarkup:
    rows = []
    for cat in categories:
        rows.append([InlineKeyboardButton(
            text=f"{cat['emoji']} {cat['name']}",
            callback_data=f"cat_open:{cat['id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


# ── Листалка товаров: карточка товара с навигацией ──
def kb_product_browse(product_id: int, cat_id: int, index: int, total: int, lang: str) -> InlineKeyboardMarkup:
    """Клавиатура для листалки: стрелки + корзина + назад к категориям."""
    nav_row = []
    if index > 0:
        nav_row.append(InlineKeyboardButton(
            text="◀️",
            callback_data=f"browse:{cat_id}:{index - 1}"
        ))
    nav_row.append(InlineKeyboardButton(
        text=f"{index + 1} / {total}",
        callback_data="noop"
    ))
    if index < total - 1:
        nav_row.append(InlineKeyboardButton(
            text="▶️",
            callback_data=f"browse:{cat_id}:{index + 1}"
        ))

    rows = [
        nav_row,
        [InlineKeyboardButton(text=t("add_to_cart", lang), callback_data=f"buy:{product_id}:{cat_id}")],
        [InlineKeyboardButton(text=t("back_to_catalog", lang), callback_data="catalog_back")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_sizes(sizes: list, product_id: int, cat_id: int) -> InlineKeyboardMarkup:
    rows = []
    row = []
    for i, size in enumerate(sizes):
        row.append(InlineKeyboardButton(
            text=size, callback_data=f"size:{product_id}:{cat_id}:{size}"
        ))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_colors(colors: list, product_id: int, cat_id: int, size: str) -> InlineKeyboardMarkup:
    rows = []
    row = []
    for color in colors:
        row.append(InlineKeyboardButton(
            text=color, callback_data=f"color:{product_id}:{cat_id}:{size}:{color}"
        ))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_after_add_to_cart(cat_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("go_to_cart", lang), callback_data="go_to_cart")],
        [InlineKeyboardButton(text=t("continue_shopping", lang), callback_data=f"cat_open:{cat_id}")],
    ])


def kb_cart(cart_items, lang: str) -> InlineKeyboardMarkup:
    rows = []
    for item in cart_items:
        rows.append([
            InlineKeyboardButton(text="➖", callback_data=f"cart_dec:{item['id']}"),
            InlineKeyboardButton(
                text=f"{item['name'][:15]} {item['size']} {item['color']} ×{item['quantity']}",
                callback_data="noop"
            ),
            InlineKeyboardButton(text="➕", callback_data=f"cart_inc:{item['id']}"),
            InlineKeyboardButton(text="🗑", callback_data=f"cart_del:{item['id']}"),
        ])
    rows.append([
        InlineKeyboardButton(text=t("clear_cart", lang), callback_data="cart_clear"),
        InlineKeyboardButton(text=t("checkout", lang), callback_data="checkout"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_confirm_order(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("confirm", lang), callback_data="order_confirm"),
            InlineKeyboardButton(text=t("cancel", lang), callback_data="order_cancel"),
        ]
    ])


def kb_payment(order_id: int, payment_link: str, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("pay_button", lang), url=payment_link)],
        [InlineKeyboardButton(text=t("paid_button", lang), callback_data=f"paid:{order_id}")],
    ])


def kb_admin_order(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin_confirm:{order_id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"admin_reject:{order_id}"),
        ]
    ])


def kb_skip(lang: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t("skip", lang))]],
        resize_keyboard=True,
        one_time_keyboard=True
    )


def kb_admin_main() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Товары"), KeyboardButton(text="🗂 Категории")],
            [KeyboardButton(text="📦 Заказы"), KeyboardButton(text="🎟 Промокоды")],
            [KeyboardButton(text="👥 Клиенты"), KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="📢 Рассылка"), KeyboardButton(text="⚙️ Настройки")],
            [KeyboardButton(text="🔧 Тех. перерыв"), KeyboardButton(text="🏠 Выход из панели")],
        ],
        resize_keyboard=True
    )


def kb_admin_products(products) -> InlineKeyboardMarkup:
    rows = []
    for p in products:
        status = "✅" if p["is_active"] else "🚫"
        cat = f"[{p['cat_name']}] " if p["cat_name"] else ""
        rows.append([InlineKeyboardButton(
            text=f"{status} {cat}{p['name']} — {p['price']:.0f} ₽",
            callback_data=f"adm_prod:{p['id']}"
        )])
    rows.append([InlineKeyboardButton(text="➕ Быстро добавить товар", callback_data="adm_quick_add")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_admin_product_actions(product_id: int, is_active: int) -> InlineKeyboardMarkup:
    toggle_text = "🚫 Скрыть" if is_active else "✅ Показать"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"adm_edit:{product_id}"),
            InlineKeyboardButton(text="📦 Остатки", callback_data=f"adm_stock:{product_id}"),
        ],
        [
            InlineKeyboardButton(text=toggle_text, callback_data=f"adm_toggle:{product_id}"),
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"adm_del:{product_id}"),
        ],
        [InlineKeyboardButton(text="⬅️ К списку товаров", callback_data="adm_back_products")],
    ])


def kb_admin_edit_fields(product_id: int) -> InlineKeyboardMarkup:
    fields = [
        ("📝 Название", "name"), ("📄 Описание", "description"),
        ("💰 Цена", "price"), ("🏷 Старая цена", "old_price"),
        ("📐 Размеры", "sizes"), ("🎨 Цвета", "colors"),
        ("🖼 Фото", "photos"), ("🗂 Категория", "category_id"),
    ]
    rows = []
    for i in range(0, len(fields), 2):
        row = []
        for label, field in fields[i:i+2]:
            row.append(InlineKeyboardButton(
                text=label, callback_data=f"adm_ef:{product_id}:{field}"
            ))
        rows.append(row)
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"adm_prod:{product_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_admin_promos(promos) -> InlineKeyboardMarkup:
    rows = []
    for p in promos:
        status = "✅" if p["is_active"] else "🚫"
        disc = f"{p['value']:.0f}%" if p["type"] == "percent" else f"{p['value']:.0f} ₽"
        rows.append([
            InlineKeyboardButton(
                text=f"{status} {p['code']} −{disc}",
                callback_data=f"adm_promo:{p['id']}"
            )
        ])
    rows.append([InlineKeyboardButton(text="➕ Добавить промокод", callback_data="adm_add_promo")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_admin_promo_actions(promo_id: int, is_active: int) -> InlineKeyboardMarkup:
    toggle_text = "🚫 Выключить" if is_active else "✅ Включить"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=toggle_text, callback_data=f"adm_promo_toggle:{promo_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"adm_promo_del:{promo_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm_back_promos")],
    ])


def kb_admin_orders(orders) -> InlineKeyboardMarkup:
    rows = []
    status_map = {
        "pending": "⏳", "paid": "💳", "confirmed": "✅", "rejected": "❌"
    }
    for o in orders[:20]:
        icon = status_map.get(o["status"], "❓")
        rows.append([InlineKeyboardButton(
            text=f"{icon} #{o['id']} {o['name']} — {o['total']:.0f} ₽",
            callback_data=f"adm_order:{o['id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_admin_categories(categories) -> InlineKeyboardMarkup:
    rows = []
    for cat in categories:
        status = "✅" if cat["is_active"] else "🚫"
        rows.append([InlineKeyboardButton(
            text=f"{status} {cat['emoji']} {cat['name']}",
            callback_data=f"adm_cat:{cat['id']}"
        )])
    rows.append([InlineKeyboardButton(text="➕ Добавить категорию", callback_data="adm_add_cat")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_admin_category_actions(cat_id: int, is_active: int) -> InlineKeyboardMarkup:
    toggle_text = "🚫 Скрыть" if is_active else "✅ Показать"
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"adm_cat_edit:{cat_id}"),
            InlineKeyboardButton(text=toggle_text, callback_data=f"adm_cat_toggle:{cat_id}"),
        ],
        [InlineKeyboardButton(text="🗑 Удалить категорию", callback_data=f"adm_cat_del:{cat_id}")],
        [InlineKeyboardButton(text="⬅️ К списку категорий", callback_data="adm_back_cats")],
    ])


def kb_select_category_for_product(categories) -> InlineKeyboardMarkup:
    rows = []
    for cat in categories:
        rows.append([InlineKeyboardButton(
            text=f"{cat['emoji']} {cat['name']}",
            callback_data=f"adm_prod_cat:{cat['id']}"
        )])
    rows.append([InlineKeyboardButton(text="📦 Без категории", callback_data="adm_prod_cat:0")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_maintenance_actions(is_on: bool) -> InlineKeyboardMarkup:
    if is_on:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Открыть магазин", callback_data="maint_off")],
            [InlineKeyboardButton(text="✏️ Изменить время", callback_data="maint_set_time")],
            [InlineKeyboardButton(text="📢 Рассылка о перерыве", callback_data="maint_broadcast")],
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔧 Закрыть на тех. перерыв", callback_data="maint_on")],
        ])


def kb_admin_user_actions(tg_id: int, is_banned: int) -> InlineKeyboardMarkup:
    ban_text = "✅ Разбанить" if is_banned else "🚫 Забанить"
    ban_cb = f"adm_unban:{tg_id}" if is_banned else f"adm_ban:{tg_id}"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=ban_text, callback_data=ban_cb)],
        [InlineKeyboardButton(text="✉️ Написать пользователю", callback_data=f"adm_msg_user:{tg_id}")],
        [InlineKeyboardButton(text="📝 Добавить заметку", callback_data=f"adm_note:{tg_id}")],
        [InlineKeyboardButton(text="📦 Заказы пользователя", callback_data=f"adm_user_orders:{tg_id}")],
        [InlineKeyboardButton(text="⬅️ Назад к клиентам", callback_data="adm_back_clients")],
    ])


def kb_admin_clients_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Все клиенты", callback_data="adm_clients_list:0")],
        [InlineKeyboardButton(text="🚫 Забаненные", callback_data="adm_clients_banned")],
        [InlineKeyboardButton(text="🔍 Поиск по username / ID", callback_data="adm_clients_search")],
    ])


# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────

def calc_cart_total(cart_items) -> float:
    return sum(item["price"] * item["quantity"] for item in cart_items)


def format_items_for_order(cart_items) -> list:
    return [
        {
            "product_id": item["product_id"],
            "name": item["name"],
            "size": item["size"],
            "color": item["color"],
            "quantity": item["quantity"],
            "price": item["price"],
        }
        for item in cart_items
    ]


def format_order_items_text(items: list) -> str:
    lines = []
    for i in items:
        lines.append(
            f"• <b>{i['name']}</b> | {i['size']} | {i['color']} ×{i['quantity']} "
            f"— {i['price'] * i['quantity']:.2f} ₽"
        )
    return "\n".join(lines)


def apply_discount(total: float, promo: sqlite3.Row) -> tuple:
    if promo["type"] == "percent":
        discount = round(total * promo["value"] / 100, 2)
        discount_str = f"{promo['value']:.0f}%"
    else:
        discount = min(promo["value"], total)
        discount_str = f"{promo['value']:.0f} ₽"
    return discount, discount_str


def is_admin(tg_id: int) -> bool:
    return tg_id in ADMIN_IDS


def build_cart_text(cart, lang: str) -> str:
    lines = [t("cart_header", lang)]
    for item in cart:
        lines.append(
            f"• {item['name']} | {item['size']} | {item['color']} "
            f"×{item['quantity']} = {item['price'] * item['quantity']:.2f} ₽"
        )
    total = calc_cart_total(cart)
    lines.append(t("cart_total", lang, total=f"{total:.2f}"))
    return "\n".join(lines)


def build_maintenance_text(lang: str) -> str:
    maint_time = db_get_maintenance_time()
    if maint_time:
        time_info = t("maintenance_time", lang, time=maint_time)
    else:
        time_info = ""
    return t("maintenance", lang, time_info=time_info)


def build_product_caption(product) -> str:
    """Формирует текст карточки товара."""
    photos = json.loads(product["photos"])
    sizes = json.loads(product["sizes"])
    colors = json.loads(product["colors"])

    old_price_line = ""
    if product["old_price"] and product["old_price"] > 0:
        old_price_line = f"\n<s>{product['old_price']:.0f} ₽</s>"

    caption = (
        f"<b>{product['name']}</b>\n\n"
        f"{product['description'] or ''}"
        f"{old_price_line}\n"
        f"💰 <b>{product['price']:.0f} ₽</b>\n\n"
        f"📐 Размеры: {', '.join(sizes)}\n"
        f"🎨 Цвета: {', '.join(colors)}"
    )
    return caption


async def send_product_card(message_or_call, product, cat_id: int, index: int, total: int, lang: str):
    """Отправляет карточку товара с навигацией (новым сообщением)."""
    photos = json.loads(product["photos"])
    caption = build_product_caption(product)
    kb = kb_product_browse(product["id"], cat_id, index, total, lang)

    first_photo = photos[0] if photos else None
    if first_photo:
        await message_or_call.answer_photo(
            photo=first_photo,
            caption=caption,
            reply_markup=kb
        )
    else:
        await message_or_call.answer(caption, reply_markup=kb)


# ─────────────────────────────────────────────
# BOT SETUP
# ─────────────────────────────────────────────

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
router = Router()
dp.include_router(router)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# USER HANDLERS
# ─────────────────────────────────────────────

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    tg_id = message.from_user.id

    # Проверка бана
    if not is_admin(tg_id) and db_is_banned(tg_id):
        lang = db_get_lang(tg_id) or "ru"
        await message.answer(t("banned_message", lang))
        return

    # Admins bypass maintenance
    if not is_admin(tg_id) and db_is_maintenance():
        lang = db_get_lang(tg_id) or "ru"
        text = build_maintenance_text(lang)
        if os.path.exists(LOGO_PATH):
            photo = FSInputFile(LOGO_PATH)
            await message.answer_photo(photo=photo, caption=text)
        else:
            await message.answer(text)
        return

    user = db_get_user(tg_id)
    db_upsert_user(
        tg_id,
        message.from_user.username or "",
        message.from_user.first_name or "",
        message.from_user.last_name or "",
    )

    if not user or not user["lang"]:
        await state.set_state(LangState.choosing)
        welcome_text = T["welcome_img"].get("ru")
        if os.path.exists(LOGO_PATH):
            photo = FSInputFile(LOGO_PATH)
            await message.answer_photo(
                photo=photo,
                caption=welcome_text,
                reply_markup=kb_lang_select()
            )
        else:
            await message.answer(welcome_text, reply_markup=kb_lang_select())
    else:
        lang = user["lang"]
        await message.answer(
            t("main_menu", lang),
            reply_markup=kb_main_menu(lang)
        )


@router.callback_query(LangState.choosing, F.data.startswith("lang:"))
async def cb_lang_chosen(call: CallbackQuery, state: FSMContext):
    lang = call.data.split(":")[1]
    if lang not in LANGUAGES:
        await call.answer()
        return
    db_set_lang(call.from_user.id, lang)
    await state.clear()
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await call.message.answer(
        t("language_saved", lang) + "\n\n" + t("main_menu", lang),
        reply_markup=kb_main_menu(lang)
    )
    await call.answer()


def _collect_translations(key: str) -> set:
    result = set()
    for value in T.get(key, {}).values():
        if value:
            result.add(value)
    return result


CATALOG_TEXTS = _collect_translations("catalog")
CART_TEXTS = _collect_translations("cart")
MY_ORDERS_TEXTS = _collect_translations("my_orders")
SETTINGS_TEXTS = _collect_translations("settings")

ALL_MENU_TEXTS = CATALOG_TEXTS | CART_TEXTS | MY_ORDERS_TEXTS | SETTINGS_TEXTS


@router.message(StateFilter(None), F.text.in_(ALL_MENU_TEXTS))
async def handle_main_menu_buttons(message: Message, state: FSMContext):
    tg_id = message.from_user.id

    # Проверка бана
    if not is_admin(tg_id) and db_is_banned(tg_id):
        lang = db_get_lang(tg_id) or "ru"
        await message.answer(t("banned_message", lang))
        return

    lang = db_get_lang(tg_id)
    text = message.text

    if text in CATALOG_TEXTS:
        categories = db_get_active_categories()
        if not categories:
            await message.answer(t("no_categories", lang))
            return
        await message.answer(
            t("choose_category", lang),
            reply_markup=kb_categories(categories, lang)
        )
        return

    if text in CART_TEXTS:
        cart = db_get_cart(tg_id)
        if not cart:
            await message.answer(t("cart_empty", lang))
            return
        await message.answer(build_cart_text(cart, lang), reply_markup=kb_cart(cart, lang))
        return

    if text in MY_ORDERS_TEXTS:
        orders = db_get_user_orders(tg_id)
        if not orders:
            await message.answer(t("no_orders", lang))
            return
        status_map = {
            "pending": t("order_status_pending", lang),
            "paid": t("order_status_paid", lang),
            "confirmed": t("order_status_confirmed", lang),
            "rejected": t("order_status_rejected", lang),
        }
        lines = ["📦 <b>Ваши заказы:</b>\n"]
        for o in orders[:10]:
            status = status_map.get(o["status"], o["status"])
            items = json.loads(o["items"])
            items_short = ", ".join(f"{i['name']} ×{i['quantity']}" for i in items)
            lines.append(
                f"<b>Заказ #{o['id']}</b>\n"
                f"├ Статус: {status}\n"
                f"├ {items_short}\n"
                f"├ 💰 {o['total']:.2f} ₽\n"
                f"└ 📅 {o['created_at'][:10]}\n"
            )
        await message.answer("\n".join(lines))
        return

    if text in SETTINGS_TEXTS:
        await message.answer(
            f"⚙️ <b>{t('settings', lang)}</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t("change_language", lang), callback_data="change_lang")]
            ])
        )
        return


@router.callback_query(F.data == "catalog_back")
async def cb_catalog_back(call: CallbackQuery):
    lang = db_get_lang(call.from_user.id)
    categories = db_get_active_categories()
    if not categories:
        try:
            await call.message.edit_text(t("no_categories", lang))
        except Exception:
            await call.message.answer(t("no_categories", lang))
        await call.answer()
        return
    try:
        await call.message.edit_text(
            t("choose_category", lang),
            reply_markup=kb_categories(categories, lang)
        )
    except Exception:
        # Если предыдущее сообщение было с фото — удаляем и отправляем новое
        try:
            await call.message.delete()
        except Exception:
            pass
        await call.message.answer(
            t("choose_category", lang),
            reply_markup=kb_categories(categories, lang)
        )
    await call.answer()


# ── ОТКРЫТИЕ КАТЕГОРИИ — сразу показываем первый товар ──
@router.callback_query(F.data.startswith("cat_open:"))
async def cb_cat_open(call: CallbackQuery):
    cat_id = int(call.data.split(":")[1])
    lang = db_get_lang(call.from_user.id)
    category = db_get_category(cat_id)
    if not category:
        await call.answer("Категория не найдена")
        return

    products = db_get_products_by_category(cat_id)
    if not products:
        try:
            await call.message.edit_text(
                f"{category['emoji']} <b>{category['name']}</b>\n\n{t('catalog_empty', lang)}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=t("back", lang), callback_data="catalog_back")]
                ])
            )
        except Exception:
            try:
                await call.message.delete()
            except Exception:
                pass
            await call.message.answer(
                f"{category['emoji']} <b>{category['name']}</b>\n\n{t('catalog_empty', lang)}",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=t("back", lang), callback_data="catalog_back")]
                ])
            )
        await call.answer()
        return

    # Удаляем предыдущее сообщение и показываем первый товар
    try:
        await call.message.delete()
    except Exception:
        pass

    await send_product_card(call.message, products[0], cat_id, 0, len(products), lang)
    await call.answer()


# ── ЛИСТАЛКА: переход к товару по индексу ──
@router.callback_query(F.data.startswith("browse:"))
async def cb_browse(call: CallbackQuery):
    parts = call.data.split(":")
    cat_id = int(parts[1])
    index = int(parts[2])
    lang = db_get_lang(call.from_user.id)

    products = db_get_products_by_category(cat_id)
    if not products or index >= len(products) or index < 0:
        await call.answer("Товар не найден")
        return

    product = products[index]
    photos = json.loads(product["photos"])
    caption = build_product_caption(product)
    kb = kb_product_browse(product["id"], cat_id, index, len(products), lang)

    first_photo = photos[0] if photos else None

    # Пытаемся отредактировать медиа, если фото есть
    if first_photo:
        try:
            await call.message.edit_media(
                media=InputMediaPhoto(media=first_photo, caption=caption),
                reply_markup=kb
            )
        except Exception:
            # Если не получается — удаляем и отправляем новое
            try:
                await call.message.delete()
            except Exception:
                pass
            await call.message.answer_photo(
                photo=first_photo,
                caption=caption,
                reply_markup=kb
            )
    else:
        try:
            await call.message.edit_text(caption, reply_markup=kb)
        except Exception:
            try:
                await call.message.delete()
            except Exception:
                pass
            await call.message.answer(caption, reply_markup=kb)

    await call.answer()


@router.callback_query(F.data.startswith("buy:"))
async def cb_buy(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    product_id = int(parts[1])
    cat_id = int(parts[2]) if len(parts) > 2 else 0
    lang = db_get_lang(call.from_user.id)
    product = db_get_product(product_id)
    if not product:
        await call.answer("Товар не найден")
        return

    sizes = json.loads(product["sizes"])
    if not sizes:
        await call.answer("Нет доступных размеров", show_alert=True)
        return

    await state.set_state(ProductState.selecting_size)
    await state.update_data(product_id=product_id, cat_id=cat_id)
    await call.message.answer(
        t("select_size", lang),
        reply_markup=kb_sizes(sizes, product_id, cat_id)
    )
    await call.answer()


@router.callback_query(ProductState.selecting_size, F.data.startswith("size:"))
async def cb_select_size(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    product_id = int(parts[1])
    cat_id = int(parts[2])
    size = parts[3]
    lang = db_get_lang(call.from_user.id)
    product = db_get_product(product_id)
    if not product:
        await call.answer()
        return

    colors = json.loads(product["colors"])
    await state.update_data(size=size, cat_id=cat_id)
    await state.set_state(ProductState.selecting_color)
    await call.message.answer(
        t("select_color", lang),
        reply_markup=kb_colors(colors, product_id, cat_id, size)
    )
    await call.answer()


@router.callback_query(ProductState.selecting_color, F.data.startswith("color:"))
async def cb_select_color(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    product_id = int(parts[1])
    cat_id = int(parts[2])
    size = parts[3]
    color = parts[4]
    tg_id = call.from_user.id
    lang = db_get_lang(tg_id)

    stock = db_get_stock(product_id, size, color)
    if stock <= 0:
        await call.answer(t("out_of_stock", lang), show_alert=True)
        return

    db_add_to_cart(tg_id, product_id, size, color)
    await state.clear()
    data_state = await state.get_data()
    cat_id_for_back = data_state.get("cat_id", cat_id)
    await call.message.answer(
        t("added_to_cart", lang),
        reply_markup=kb_after_add_to_cart(cat_id_for_back, lang)
    )
    await call.answer()


@router.callback_query(F.data == "go_to_cart")
async def cb_go_to_cart(call: CallbackQuery, state: FSMContext):
    await state.clear()
    tg_id = call.from_user.id
    lang = db_get_lang(tg_id)
    cart = db_get_cart(tg_id)
    if not cart:
        await call.message.answer(t("cart_empty", lang))
        await call.answer()
        return
    text = build_cart_text(cart, lang)
    await call.message.answer(text, reply_markup=kb_cart(cart, lang))
    await call.answer()


# ─────── CART CALLBACKS ───────

@router.callback_query(F.data.startswith("cart_dec:"))
async def cb_cart_dec(call: CallbackQuery):
    cart_id = int(call.data.split(":")[1])
    conn = get_db()
    row = conn.execute("SELECT quantity FROM cart WHERE id=?", (cart_id,)).fetchone()
    conn.close()
    if row:
        db_update_cart_qty(cart_id, row["quantity"] - 1)
    lang = db_get_lang(call.from_user.id)
    cart = db_get_cart(call.from_user.id)
    if not cart:
        await call.message.edit_text(t("cart_empty", lang))
        await call.answer()
        return
    text = build_cart_text(cart, lang)
    await call.message.edit_text(text, reply_markup=kb_cart(cart, lang))
    await call.answer()


@router.callback_query(F.data.startswith("cart_inc:"))
async def cb_cart_inc(call: CallbackQuery):
    cart_id = int(call.data.split(":")[1])
    conn = get_db()
    row = conn.execute(
        "SELECT quantity, product_id, size, color FROM cart WHERE id=?", (cart_id,)
    ).fetchone()
    conn.close()
    lang = db_get_lang(call.from_user.id)
    if row:
        stock = db_get_stock(row["product_id"], row["size"], row["color"])
        if row["quantity"] >= stock:
            await call.answer(t("out_of_stock", lang), show_alert=True)
            return
        db_update_cart_qty(cart_id, row["quantity"] + 1)
    cart = db_get_cart(call.from_user.id)
    text = build_cart_text(cart, lang)
    await call.message.edit_text(text, reply_markup=kb_cart(cart, lang))
    await call.answer()


@router.callback_query(F.data.startswith("cart_del:"))
async def cb_cart_del(call: CallbackQuery):
    cart_id = int(call.data.split(":")[1])
    db_remove_from_cart(cart_id)
    lang = db_get_lang(call.from_user.id)
    cart = db_get_cart(call.from_user.id)
    if not cart:
        await call.message.edit_text(t("cart_empty", lang))
        await call.answer()
        return
    text = build_cart_text(cart, lang)
    await call.message.edit_text(text, reply_markup=kb_cart(cart, lang))
    await call.answer()


@router.callback_query(F.data == "cart_clear")
async def cb_cart_clear(call: CallbackQuery):
    db_clear_cart(call.from_user.id)
    lang = db_get_lang(call.from_user.id)
    await call.message.edit_text(t("cart_cleared", lang))
    await call.answer()


# ─────── CHECKOUT ───────

@router.callback_query(F.data == "checkout")
async def cb_checkout(call: CallbackQuery, state: FSMContext):
    tg_id = call.from_user.id
    lang = db_get_lang(tg_id)
    cart = db_get_cart(tg_id)
    if not cart:
        await call.answer(t("cart_empty", lang), show_alert=True)
        return
    await state.set_state(CheckoutState.name)
    await call.message.answer(t("enter_name", lang), reply_markup=ReplyKeyboardRemove())
    await call.answer()


@router.message(CheckoutState.name)
async def checkout_name(message: Message, state: FSMContext):
    lang = db_get_lang(message.from_user.id)
    if len(message.text.strip()) < 2:
        await message.answer("⚠️ Введите корректное имя:")
        return
    await state.update_data(name=message.text.strip())
    await state.set_state(CheckoutState.phone)
    await message.answer(t("enter_phone", lang))


@router.message(CheckoutState.phone)
async def checkout_phone(message: Message, state: FSMContext):
    lang = db_get_lang(message.from_user.id)
    await state.update_data(phone=message.text.strip())
    await state.set_state(CheckoutState.address)
    await message.answer(t("enter_address", lang))


@router.message(CheckoutState.address)
async def checkout_address(message: Message, state: FSMContext):
    lang = db_get_lang(message.from_user.id)
    if len(message.text.strip()) < 5:
        await message.answer("⚠️ Введите полный адрес доставки:")
        return
    await state.update_data(address=message.text.strip())
    await state.set_state(CheckoutState.promo)
    await message.answer(t("enter_promo", lang), reply_markup=kb_skip(lang))


@router.message(CheckoutState.promo)
async def checkout_promo(message: Message, state: FSMContext):
    lang = db_get_lang(message.from_user.id)
    skip_text = t("skip", lang)
    text = message.text.strip()

    promo_code = None
    discount_amount = 0.0
    discount_str = ""

    if text != skip_text and text:
        promo = db_get_promo(text)
        if promo:
            tg_id = message.from_user.id
            cart = db_get_cart(tg_id)
            total_raw = calc_cart_total(cart)
            discount_amount, discount_str = apply_discount(total_raw, promo)
            promo_code = promo["code"]
            await message.answer(t("promo_applied", lang, discount=discount_str))
        else:
            await message.answer(t("promo_invalid", lang), reply_markup=kb_skip(lang))
            return

    await state.update_data(
        promo_code=promo_code,
        discount_amount=discount_amount,
        discount_str=discount_str
    )
    data = await state.get_data()
    tg_id = message.from_user.id
    cart = db_get_cart(tg_id)
    total_raw = calc_cart_total(cart)
    total = max(0.0, total_raw - discount_amount)

    items_text = format_order_items_text(format_items_for_order(cart))
    promo_line = ""
    if promo_code:
        promo_line = t("promo_label", lang, code=promo_code, discount=discount_str)

    confirm_text = t(
        "order_confirm", lang,
        items=items_text,
        name=data["name"],
        phone=data["phone"],
        address=data["address"],
        promo_line=promo_line,
        total=f"{total:.2f}"
    )

    await state.update_data(total=total)
    await state.set_state(CheckoutState.confirm)
    await message.answer(
        confirm_text,
        reply_markup=kb_confirm_order(lang)
    )


@router.callback_query(CheckoutState.confirm, F.data == "order_confirm")
async def cb_order_confirm(call: CallbackQuery, state: FSMContext):
    tg_id = call.from_user.id
    lang = db_get_lang(tg_id)
    data = await state.get_data()
    cart = db_get_cart(tg_id)

    if not cart:
        await call.answer(t("cart_empty", lang), show_alert=True)
        await state.clear()
        return

    items = format_items_for_order(cart)

    order_id = db_create_order(
        tg_id=tg_id,
        name=data["name"],
        phone=data["phone"],
        address=data["address"],
        items=items,
        promo_code=data.get("promo_code") or "",
        discount_amount=data.get("discount_amount", 0.0),
        total=data["total"]
    )

    db_clear_cart(tg_id)
    await state.clear()

    payment_link = db_get_setting("payment_link") or DEFAULT_PAYMENT_LINK

    await call.message.answer(
        t("order_placed", lang, order_id=order_id),
        reply_markup=kb_payment(order_id, payment_link, lang)
    )
    await call.message.answer(t("main_menu", lang), reply_markup=kb_main_menu(lang))
    await call.answer()


@router.callback_query(CheckoutState.confirm, F.data == "order_cancel")
async def cb_order_cancel(call: CallbackQuery, state: FSMContext):
    lang = db_get_lang(call.from_user.id)
    await state.clear()
    await call.message.answer(t("main_menu", lang), reply_markup=kb_main_menu(lang))
    await call.answer()


# ─────── PAYMENT ───────

@router.callback_query(F.data.startswith("paid:"))
async def cb_paid(call: CallbackQuery):
    order_id = int(call.data.split(":")[1])
    tg_id = call.from_user.id
    lang = db_get_lang(tg_id)
    order = db_get_order(order_id)

    if not order or order["tg_id"] != tg_id:
        await call.answer("Заказ не найден", show_alert=True)
        return

    if order["status"] != "pending":
        await call.answer("Заявка уже отправлена ранее.", show_alert=True)
        return

    db_set_order_status(order_id, "paid")

    items = json.loads(order["items"])
    user = db_get_user(tg_id)
    username_str = f"@{user['username']}" if user and user["username"] else "—"
    items_text = format_order_items_text(items)
    promo_info = ""
    if order["promo_code"]:
        promo_info = f"\n🎟 Промокод: {order['promo_code']} (−{order['discount_amount']:.2f} ₽)"

    admin_text = (
        f"🔔 <b>Новая заявка на подтверждение оплаты!</b>\n\n"
        f"📦 Заказ <b>#{order_id}</b>\n\n"
        f"👤 Имя: {order['name']}\n"
        f"🧑 Username: {username_str}\n"
        f"🆔 Telegram ID: <code>{tg_id}</code>\n"
        f"📱 Телефон: {order['phone']}\n"
        f"📍 Адрес: {order['address']}\n\n"
        f"🛍 <b>Товары:</b>\n{items_text}"
        f"{promo_info}\n\n"
        f"💰 <b>Итого: {order['total']:.2f} ₽</b>\n"
        f"📅 {order['created_at'][:16]}"
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, admin_text, reply_markup=kb_admin_order(order_id))
        except Exception:
            pass

    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await call.message.answer(t("paid_confirm_msg", lang))
    await call.answer()


# ─────── ADMIN ORDER CONFIRM/REJECT ───────

@router.callback_query(F.data.startswith("admin_confirm:"))
async def cb_admin_confirm(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return
    order_id = int(call.data.split(":")[1])
    order = db_get_order(order_id)
    if not order:
        await call.answer("Заказ не найден")
        return
    if order["status"] == "confirmed":
        await call.answer("Заказ уже подтверждён", show_alert=True)
        return

    db_set_order_status(order_id, "confirmed")

    items = json.loads(order["items"])
    for item in items:
        new_stock = db_decrement_stock(
            item["product_id"], item["size"], item["color"], item["quantity"]
        )
        if new_stock < 3:
            try:
                await bot.send_message(
                    call.from_user.id,
                    f"⚠️ <b>Мало товара на складе!</b>\n"
                    f"Товар: {item['name']}\n"
                    f"Размер: {item['size']} | Цвет: {item['color']}\n"
                    f"Остаток: {new_stock} шт."
                )
            except Exception:
                pass

    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await call.message.answer(f"✅ Заказ #{order_id} подтверждён.")
    lang = db_get_lang(order["tg_id"])
    try:
        await bot.send_message(
            order["tg_id"],
            t("order_approved", lang, order_id=order_id, shop=SHOP_NAME)
        )
    except Exception:
        pass
    await call.answer()


@router.callback_query(F.data.startswith("admin_reject:"))
async def cb_admin_reject(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        await call.answer("Нет доступа", show_alert=True)
        return
    order_id = int(call.data.split(":")[1])
    order = db_get_order(order_id)
    if not order:
        await call.answer("Заказ не найден")
        return
    if order["status"] == "rejected":
        await call.answer("Заказ уже отклонён", show_alert=True)
        return
    db_set_order_status(order_id, "rejected")
    try:
        await call.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await call.message.answer(f"❌ Заказ #{order_id} отклонён.")
    lang = db_get_lang(order["tg_id"])
    try:
        await bot.send_message(
            order["tg_id"],
            t("order_rejected", lang, order_id=order_id)
        )
    except Exception:
        pass
    await call.answer()


# ─────── SETTINGS CALLBACK ───────

@router.callback_query(F.data == "change_lang")
async def cb_change_lang(call: CallbackQuery, state: FSMContext):
    lang = db_get_lang(call.from_user.id)
    await state.set_state(LangState.choosing)
    await call.message.answer(T["welcome_img"].get(lang, T["welcome_img"]["en"]), reply_markup=kb_lang_select())
    await call.answer()


# ─────────────────────────────────────────────
# ADMIN: ПАРОЛЬ НА ВХОД
# ─────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await state.set_state(AdminPasswordState.waiting)
    await message.answer(
        "🔐 <b>Введите пароль для входа в панель администратора:</b>",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(AdminPasswordState.waiting)
async def admin_password_check(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    if message.text.strip() == ADMIN_PASSWORD:
        await state.clear()
        is_maint = db_is_maintenance()
        maint_status = "🔴 Закрыт (тех. перерыв)" if is_maint else "🟢 Открыт"
        await message.answer(
            f"✅ <b>Добро пожаловать в панель администратора {SHOP_NAME}!</b>\n\n"
            f"Статус магазина: {maint_status}\n\n"
            f"Выберите раздел:",
            reply_markup=kb_admin_main()
        )
    else:
        await state.clear()
        await message.answer("❌ <b>Неверный пароль.</b> Доступ запрещён.")


@router.message(StateFilter(None), F.text == "🏠 Выход из панели")
async def admin_exit(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    lang = db_get_lang(message.from_user.id)
    await message.answer(t("main_menu", lang), reply_markup=kb_main_menu(lang))


# ─────────────────────────────────────────────
# ADMIN: MAINTENANCE
# ─────────────────────────────────────────────

@router.message(StateFilter(None), F.text == "🔧 Тех. перерыв")
async def admin_maintenance(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    is_on = db_is_maintenance()
    maint_time = db_get_maintenance_time()

    status_text = "🔴 <b>Магазин ЗАКРЫТ</b> (тех. перерыв)" if is_on else "🟢 <b>Магазин ОТКРЫТ</b>"
    time_text = f"\n⏱ Время перерыва: <b>{maint_time}</b>" if maint_time else ""

    await message.answer(
        f"🔧 <b>Технический перерыв</b>\n\n"
        f"Статус: {status_text}{time_text}\n\n"
        f"При включённом тех. перерыве пользователи будут видеть сообщение о закрытии при /start.",
        reply_markup=kb_maintenance_actions(is_on)
    )


@router.callback_query(F.data == "maint_on")
async def cb_maint_on(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(AdminMaintenance.set_time)
    await call.message.answer(
        "⏱ Введите примерное время тех. перерыва (например: <b>30 минут</b>, <b>1-2 часа</b>, <b>до 20:00</b>).\n\n"
        "Или отправьте <b>-</b> чтобы не указывать время:",
        reply_markup=ReplyKeyboardRemove()
    )
    await call.answer()


@router.message(AdminMaintenance.set_time)
async def adm_maintenance_time(message: Message, state: FSMContext):
    time_str = message.text.strip()
    if time_str == "-":
        time_str = ""
    db_set_setting("maintenance_time", time_str)
    db_set_setting("maintenance", "1")
    await state.clear()

    time_info = f" Время: <b>{time_str}</b>" if time_str else ""
    await message.answer(
        f"🔴 <b>Магазин закрыт на тех. перерыв.</b>{time_info}\n\n"
        f"Пользователи будут видеть сообщение о перерыве при попытке запустить бот.",
        reply_markup=kb_admin_main()
    )
    await message.answer(
        "Хотите разослать уведомление о тех. перерыве всем пользователям?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Да, разослать", callback_data="maint_broadcast"),
                InlineKeyboardButton(text="❌ Нет", callback_data="noop"),
            ]
        ])
    )


@router.callback_query(F.data == "maint_set_time")
async def cb_maint_set_time(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(AdminMaintenance.set_time)
    await call.message.answer(
        "⏱ Введите новое примерное время тех. перерыва (например: <b>1 час</b>, <b>до 18:00</b>).\n\n"
        "Отправьте <b>-</b> чтобы убрать время:",
        reply_markup=ReplyKeyboardRemove()
    )
    await call.answer()


@router.callback_query(F.data == "maint_off")
async def cb_maint_off(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    db_set_setting("maintenance", "0")
    db_set_setting("maintenance_time", "")
    try:
        await call.message.edit_reply_markup(reply_markup=kb_maintenance_actions(False))
    except Exception:
        pass
    await call.message.answer(
        "🟢 <b>Магазин открыт!</b> Пользователи снова могут пользоваться ботом.\n\n"
        "Хотите разослать уведомление об открытии?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Разослать об открытии", callback_data="maint_broadcast_open"),
                InlineKeyboardButton(text="❌ Нет", callback_data="noop"),
            ]
        ])
    )
    await call.answer("Магазин открыт!")


@router.callback_query(F.data == "maint_broadcast")
async def cb_maint_broadcast(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    maint_time = db_get_maintenance_time()
    users = db_get_all_users()

    time_line = f"\n⏱ Примерное время: <b>{maint_time}</b>" if maint_time else ""
    broadcast_text = (
        f"🔧 <b>Уважаемые покупатели!</b>\n\n"
        f"Магазин <b>{SHOP_NAME}</b> временно закрыт на техническое обслуживание.{time_line}\n\n"
        f"Приносим извинения за неудобства. Скоро вернёмся! ☀️"
    )

    await call.message.answer(
        f"📢 Будет отправлено <b>{len(users)}</b> пользователям:\n\n{broadcast_text}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="maint_bc_confirm:close"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="noop"),
            ]
        ])
    )
    await call.answer()


@router.callback_query(F.data == "maint_broadcast_open")
async def cb_maint_broadcast_open(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    users = db_get_all_users()
    broadcast_text = (
        f"🟢 <b>Магазин {SHOP_NAME} снова открыт!</b>\n\n"
        f"Добро пожаловать! Ждём вас в нашем каталоге. ☀️\n\n"
        f"Нажмите /start чтобы начать."
    )
    await call.message.answer(
        f"📢 Будет отправлено <b>{len(users)}</b> пользователям:\n\n{broadcast_text}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="maint_bc_confirm:open"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="noop"),
            ]
        ])
    )
    await call.answer()


@router.callback_query(F.data.startswith("maint_bc_confirm:"))
async def cb_maint_bc_confirm(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    mode = call.data.split(":")[1]
    users = db_get_all_users()
    maint_time = db_get_maintenance_time()

    if mode == "close":
        time_line = f"\n⏱ Примерное время: <b>{maint_time}</b>" if maint_time else ""
        text = (
            f"🔧 <b>Уважаемые покупатели!</b>\n\n"
            f"Магазин <b>{SHOP_NAME}</b> временно закрыт на техническое обслуживание.{time_line}\n\n"
            f"Приносим извинения за неудобства. Скоро вернёмся! ☀️"
        )
    else:
        text = (
            f"🟢 <b>Магазин {SHOP_NAME} снова открыт!</b>\n\n"
            f"Добро пожаловать! Ждём вас в нашем каталоге. ☀️\n\n"
            f"Нажмите /start чтобы начать."
        )

    await call.message.answer(f"⏳ Рассылка на {len(users)} пользователей...")
    await call.answer()

    sent = 0
    failed = 0
    for user in users:
        try:
            await bot.send_message(chat_id=user["tg_id"], text=text)
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await call.message.answer(
        f"📢 <b>Рассылка завершена!</b>\n✅ Доставлено: {sent}\n❌ Ошибок: {failed}",
        reply_markup=kb_admin_main()
    )


# ─────────────────────────────────────────────
# ADMIN: CATEGORIES
# ─────────────────────────────────────────────

@router.message(StateFilter(None), F.text == "🗂 Категории")
async def admin_categories(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    categories = db_get_all_categories()
    count = len(categories)
    await message.answer(
        f"🗂 <b>Управление категориями</b>\n\nВсего: {count}",
        reply_markup=kb_admin_categories(categories)
    )


@router.callback_query(F.data == "adm_back_cats")
async def cb_adm_back_cats(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    categories = db_get_all_categories()
    await call.message.edit_text(
        f"🗂 <b>Управление категориями</b>\n\nВсего: {len(categories)}",
        reply_markup=kb_admin_categories(categories)
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm_cat:"))
async def cb_adm_cat(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cat_id = int(call.data.split(":")[1])
    cat = db_get_category(cat_id)
    if not cat:
        await call.answer("Не найдено")
        return

    conn = get_db()
    prod_count = conn.execute(
        "SELECT COUNT(*) FROM products WHERE category_id=?", (cat_id,)
    ).fetchone()[0]
    conn.close()

    status = "✅ Активна" if cat["is_active"] else "🚫 Скрыта"
    text = (
        f"{cat['emoji']} <b>{cat['name']}</b>\n\n"
        f"Статус: {status}\n"
        f"Порядок: {cat['sort_order']}\n"
        f"Товаров: {prod_count}"
    )
    await call.message.edit_text(text, reply_markup=kb_admin_category_actions(cat_id, cat["is_active"]))
    await call.answer()


@router.callback_query(F.data == "adm_add_cat")
async def cb_adm_add_cat(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(AdminAddCategory.name)
    await call.message.answer(
        "🗂 <b>Новая категория</b>\n\nВведите <b>название</b> категории:",
        reply_markup=ReplyKeyboardRemove()
    )
    await call.answer()


@router.message(AdminAddCategory.name)
async def adm_cat_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminAddCategory.emoji)
    await message.answer(
        "Введите <b>эмодзи</b> для категории (например: 👗 👔 👟 👜 🧥):\n\nПросто отправьте один эмодзи:"
    )


@router.message(AdminAddCategory.emoji)
async def adm_cat_emoji(message: Message, state: FSMContext):
    await state.update_data(emoji=message.text.strip())
    await state.set_state(AdminAddCategory.sort_order)
    await message.answer(
        "Введите <b>порядок отображения</b> (число, меньше = выше):\nНапример: 1, 2, 3..."
    )


@router.message(AdminAddCategory.sort_order)
async def adm_cat_sort(message: Message, state: FSMContext):
    try:
        sort_order = int(message.text.strip())
    except ValueError:
        sort_order = 0
    data = await state.get_data()
    cat_id = db_add_category(data["name"], data["emoji"], sort_order)
    await state.clear()
    await message.answer(
        f"✅ Категория <b>{data['emoji']} {data['name']}</b> создана (ID: {cat_id})!",
        reply_markup=kb_admin_main()
    )


@router.callback_query(F.data.startswith("adm_cat_toggle:"))
async def cb_adm_cat_toggle(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cat_id = int(call.data.split(":")[1])
    cat = db_get_category(cat_id)
    if not cat:
        await call.answer()
        return
    new_active = 1 - cat["is_active"]
    db_update_category(cat_id, cat["name"], cat["emoji"], cat["sort_order"], new_active)
    await call.answer("Статус изменён")
    cat = db_get_category(cat_id)
    await call.message.edit_reply_markup(
        reply_markup=kb_admin_category_actions(cat_id, cat["is_active"])
    )


@router.callback_query(F.data.startswith("adm_cat_del:"))
async def cb_adm_cat_del(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    cat_id = int(call.data.split(":")[1])
    db_delete_category(cat_id)
    await call.message.edit_text("🗑 Категория удалена.")
    await call.answer()


@router.callback_query(F.data.startswith("adm_cat_edit:"))
async def cb_adm_cat_edit(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    cat_id = int(call.data.split(":")[1])
    cat = db_get_category(cat_id)
    if not cat:
        await call.answer()
        return
    await state.set_state(AdminEditCategory.field)
    await state.update_data(cat_id=cat_id)
    await call.message.answer(
        f"✏️ Редактирование категории <b>{cat['emoji']} {cat['name']}</b>\n\nЧто изменить?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📝 Название", callback_data=f"adm_cef:{cat_id}:name")],
            [InlineKeyboardButton(text="🔣 Эмодзи", callback_data=f"adm_cef:{cat_id}:emoji")],
            [InlineKeyboardButton(text="🔢 Порядок", callback_data=f"adm_cef:{cat_id}:sort_order")],
        ])
    )
    await call.answer()


@router.callback_query(AdminEditCategory.field, F.data.startswith("adm_cef:"))
async def cb_adm_cat_edit_field(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    cat_id = int(parts[1])
    field = parts[2]
    await state.update_data(cat_id=cat_id, field=field)
    await state.set_state(AdminEditCategory.value)
    prompts = {
        "name": "Введите новое название:",
        "emoji": "Введите новый эмодзи:",
        "sort_order": "Введите новый порядок (число):",
    }
    await call.message.answer(prompts.get(field, "Введите новое значение:"))
    await call.answer()


@router.message(AdminEditCategory.value)
async def adm_cat_edit_value(message: Message, state: FSMContext):
    data = await state.get_data()
    cat_id = data["cat_id"]
    field = data["field"]
    cat = db_get_category(cat_id)
    if not cat:
        await state.clear()
        return

    value_str = message.text.strip()
    name = cat["name"]
    emoji = cat["emoji"]
    sort_order = cat["sort_order"]

    if field == "name":
        name = value_str
    elif field == "emoji":
        emoji = value_str
    elif field == "sort_order":
        try:
            sort_order = int(value_str)
        except ValueError:
            await message.answer("Введите число:")
            return

    db_update_category(cat_id, name, emoji, sort_order, cat["is_active"])
    await state.clear()
    await message.answer("✅ Категория обновлена.", reply_markup=kb_admin_main())


# ─────────────────────────────────────────────
# ADMIN: PRODUCTS (список)
# ─────────────────────────────────────────────

@router.message(StateFilter(None), F.text == "🛍 Товары")
async def admin_products(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    products = db_get_all_products()
    count = len(products)
    await message.answer(
        f"🛍 <b>Управление товарами</b>\n\nВсего: {count}",
        reply_markup=kb_admin_products(products)
    )


@router.callback_query(F.data == "adm_back_products")
async def cb_adm_back_products(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    products = db_get_all_products()
    await call.message.edit_text(
        f"🛍 <b>Управление товарами</b>\n\nВсего: {len(products)}",
        reply_markup=kb_admin_products(products)
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm_prod:"))
async def cb_adm_product(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    product_id = int(call.data.split(":")[1])
    product = db_get_product(product_id)
    if not product:
        await call.answer("Товар не найден")
        return
    sizes = json.loads(product["sizes"])
    colors = json.loads(product["colors"])
    photos = json.loads(product["photos"])
    status = "✅ Активен" if product["is_active"] else "🚫 Скрыт"

    cat_name = "—"
    if product["category_id"]:
        cat = db_get_category(product["category_id"])
        if cat:
            cat_name = f"{cat['emoji']} {cat['name']}"

    text = (
        f"<b>{product['name']}</b>\n\n"
        f"📄 {product['description'] or '—'}\n\n"
        f"💰 Цена: <b>{product['price']:.2f} ₽</b>"
        + (f"  <s>{product['old_price']:.2f} ₽</s>" if product["old_price"] else "") + "\n"
        f"🗂 Категория: {cat_name}\n"
        f"📐 Размеры: {', '.join(sizes) or '—'}\n"
        f"🎨 Цвета: {', '.join(colors) or '—'}\n"
        f"🖼 Фото: {len(photos)} шт.\n"
        f"Статус: {status}"
    )
    await call.message.edit_text(
        text, reply_markup=kb_admin_product_actions(product_id, product["is_active"])
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm_toggle:"))
async def cb_adm_toggle(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    product_id = int(call.data.split(":")[1])
    product = db_get_product(product_id)
    if not product:
        await call.answer()
        return
    new_val = 1 - product["is_active"]
    db_update_product_field(product_id, "is_active", new_val)
    await call.answer("Статус изменён")
    product = db_get_product(product_id)
    await call.message.edit_reply_markup(
        reply_markup=kb_admin_product_actions(product_id, product["is_active"])
    )


@router.callback_query(F.data.startswith("adm_del:"))
async def cb_adm_delete_product(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    product_id = int(call.data.split(":")[1])
    db_delete_product(product_id)
    await call.message.edit_text("🗑 Товар удалён.")
    await call.answer()


# ─────────────────────────────────────────────
# ADMIN: БЫСТРОЕ ДОБАВЛЕНИЕ ТОВАРА
# Формат одного сообщения:
#   Название
#   Описание (может быть несколько строк)
#   ---
#   цена: 4999
#   старая цена: 5999  (необязательно)
#   размеры: S, M, L, XL
#   цвета: Чёрный, Белый
# ─────────────────────────────────────────────

QUICK_ADD_HELP = (
    "➕ <b>Быстрое добавление товара</b>\n\n"
    "Отправьте одним сообщением данные в формате:\n\n"
    "<code>Название товара\n"
    "Описание товара (любое количество строк)\n"
    "---\n"
    "цена: 4999\n"
    "старая цена: 5999\n"
    "размеры: S, M, L, XL\n"
    "цвета: Чёрный, Белый</code>\n\n"
    "<b>Обязательны:</b> название, цена, размеры, цвета\n"
    "<b>Необязательно:</b> описание, старая цена\n\n"
    "Разделитель <code>---</code> отделяет описание от параметров."
)


def parse_quick_product(text: str) -> dict | None:
    """Парсит быстрый формат добавления товара. Возвращает dict или None при ошибке."""
    result = {}
    errors = []

    if "---" in text:
        parts = text.split("---", 1)
        header = parts[0].strip()
        params_block = parts[1].strip()
    else:
        # Нет разделителя — пробуем найти параметры по ключевым словам
        lines = text.strip().splitlines()
        header_lines = []
        params_lines = []
        param_keys = ("цена:", "старая цена:", "размеры:", "цвета:", "price:", "sizes:", "colors:")
        in_params = False
        for line in lines:
            if any(line.lower().startswith(k) for k in param_keys):
                in_params = True
            if in_params:
                params_lines.append(line)
            else:
                header_lines.append(line)
        header = "\n".join(header_lines).strip()
        params_block = "\n".join(params_lines).strip()

    # Разбираем заголовок: первая строка — название, остальные — описание
    header_lines = header.splitlines()
    if not header_lines:
        return None
    result["name"] = header_lines[0].strip()
    result["description"] = "\n".join(header_lines[1:]).strip() if len(header_lines) > 1 else ""

    # Разбираем параметры
    params = {}
    for line in params_block.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            params[key.strip().lower()] = val.strip()

    # Цена
    price_raw = params.get("цена") or params.get("price") or params.get("цена (₽)")
    if not price_raw:
        errors.append("❌ Не указана цена (цена: 4999)")
    else:
        try:
            result["price"] = float(price_raw.replace(",", ".").replace("₽", "").strip())
        except ValueError:
            errors.append(f"❌ Неверный формат цены: {price_raw}")

    # Старая цена (необязательно)
    old_raw = params.get("старая цена") or params.get("old price") or params.get("старая цена (₽)")
    if old_raw:
        try:
            v = float(old_raw.replace(",", ".").replace("₽", "").strip())
            result["old_price"] = v if v > 0 else None
        except ValueError:
            result["old_price"] = None
    else:
        result["old_price"] = None

    # Размеры
    sizes_raw = params.get("размеры") or params.get("sizes")
    if not sizes_raw:
        errors.append("❌ Не указаны размеры (размеры: S, M, L)")
    else:
        result["sizes"] = [s.strip() for s in sizes_raw.split(",") if s.strip()]
        if not result["sizes"]:
            errors.append("❌ Размеры пусты")

    # Цвета
    colors_raw = params.get("цвета") or params.get("colors")
    if not colors_raw:
        errors.append("❌ Не указаны цвета (цвета: Чёрный, Белый)")
    else:
        result["colors"] = [c.strip() for c in colors_raw.split(",") if c.strip()]
        if not result["colors"]:
            errors.append("❌ Цвета пусты")

    if errors:
        result["errors"] = errors

    return result


@router.callback_query(F.data == "adm_quick_add")
async def cb_adm_quick_add(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    categories = db_get_all_categories()
    if not categories:
        await call.message.answer(
            "⚠️ Сначала создайте хотя бы одну категорию!\n\nНажмите кнопку <b>🗂 Категории</b> в меню."
        )
        await call.answer()
        return
    await state.set_state(AdminQuickAddProduct.category)
    await state.update_data(photos=[])
    await call.message.answer(
        "➕ <b>Быстрое добавление товара</b>\n\n<b>Шаг 1.</b> Выберите категорию:",
        reply_markup=kb_select_category_for_product(categories)
    )
    await call.answer()


@router.callback_query(AdminQuickAddProduct.category, F.data.startswith("adm_prod_cat:"))
async def adm_quick_cat_chosen(call: CallbackQuery, state: FSMContext):
    cat_id_str = call.data.split(":")[1]
    cat_id = int(cat_id_str) if cat_id_str != "0" else None
    await state.update_data(category_id=cat_id)
    await state.set_state(AdminQuickAddProduct.text_data)
    await call.message.answer(
        QUICK_ADD_HELP + "\n\n<b>Отправьте данные товара одним сообщением:</b>",
        reply_markup=ReplyKeyboardRemove()
    )
    await call.answer()


@router.message(AdminQuickAddProduct.text_data)
async def adm_quick_text(message: Message, state: FSMContext):
    parsed = parse_quick_product(message.text)

    if not parsed:
        await message.answer("⚠️ Не удалось распознать данные. Проверьте формат и попробуйте снова.\n\n" + QUICK_ADD_HELP)
        return

    if "errors" in parsed:
        errors_text = "\n".join(parsed["errors"])
        await message.answer(
            f"⚠️ <b>Ошибки в данных:</b>\n{errors_text}\n\nИсправьте и отправьте снова.\n\n" + QUICK_ADD_HELP
        )
        return

    await state.update_data(parsed=parsed)

    # Предпросмотр
    sizes_str = ", ".join(parsed["sizes"])
    colors_str = ", ".join(parsed["colors"])
    old_price_line = f"\n🏷 Старая цена: {parsed['old_price']:.0f} ₽" if parsed.get("old_price") else ""
    preview = (
        f"✅ <b>Данные распознаны!</b>\n\n"
        f"📝 Название: <b>{parsed['name']}</b>\n"
        f"📄 Описание: {parsed['description'] or '—'}\n"
        f"💰 Цена: <b>{parsed['price']:.0f} ₽</b>{old_price_line}\n"
        f"📐 Размеры: {sizes_str}\n"
        f"🎨 Цвета: {colors_str}\n\n"
        f"<b>Шаг 2.</b> Теперь отправьте <b>фотографии</b> товара (до 10 штук).\n"
        f"Когда загрузите все — отправьте /done"
    )
    await message.answer(preview)
    await state.set_state(AdminQuickAddProduct.photos)


@router.message(AdminQuickAddProduct.photos, F.photo)
async def adm_quick_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    if len(photos) >= 10:
        await message.answer("⚠️ Максимум 10 фотографий. Отправьте /done")
        return
    file_id = message.photo[-1].file_id
    photos.append(file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Фото {len(photos)}/10 принято. Ещё или /done")


@router.message(AdminQuickAddProduct.photos, Command("done"))
async def adm_quick_photos_done(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    if not photos:
        await message.answer("⚠️ Добавьте хотя бы одно фото!")
        return

    parsed = data["parsed"]
    sizes = parsed["sizes"]
    colors = parsed["colors"]

    example_lines = "\n".join(f"{s},{c},10" for s in sizes for c in colors)
    await state.set_state(AdminQuickAddProduct.stock)
    await message.answer(
        f"<b>Шаг 3.</b> Введите <b>остатки на складе</b>.\n\n"
        f"Формат: <code>размер,цвет,количество</code> — по одному на строку\n\n"
        f"Готовый шаблон:\n<code>{example_lines}</code>\n\n"
        f"Скопируйте, измените количество и отправьте:"
    )


@router.message(AdminQuickAddProduct.stock)
async def adm_quick_stock(message: Message, state: FSMContext):
    data = await state.get_data()
    parsed = data["parsed"]
    photos = data.get("photos", [])

    stock_data = []
    errors = []
    for line in message.text.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 3:
            size, color, qty_str = parts
            try:
                qty = int(qty_str)
                stock_data.append((size, color, qty))
            except ValueError:
                errors.append(line)
        else:
            errors.append(line)

    if errors:
        await message.answer(
            f"⚠️ Ошибки в строках:\n<code>" + "\n".join(errors) + "</code>\n\nИсправьте и попробуйте снова:"
        )
        return

    cat_id = data.get("category_id")
    product_id = db_add_product(
        name=parsed["name"],
        description=parsed["description"],
        price=parsed["price"],
        old_price=parsed.get("old_price"),
        photos=photos,
        sizes=parsed["sizes"],
        colors=parsed["colors"],
        category_id=cat_id
    )

    for size, color, qty in stock_data:
        db_set_stock(product_id, size, color, qty)

    await state.clear()

    cat_str = "—"
    if cat_id:
        cat = db_get_category(cat_id)
        if cat:
            cat_str = f"{cat['emoji']} {cat['name']}"

    await message.answer(
        f"🎉 <b>Товар успешно добавлен!</b>\n\n"
        f"📝 {parsed['name']}\n"
        f"🗂 Категория: {cat_str}\n"
        f"💰 Цена: {parsed['price']:.0f} ₽\n"
        f"🖼 Фото: {len(photos)} шт.\n"
        f"📦 ID товара: {product_id}",
        reply_markup=kb_admin_main()
    )


# ─────── ADMIN: EDIT PRODUCT ───────

@router.callback_query(F.data.startswith("adm_edit:"))
async def cb_adm_edit(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    product_id = int(call.data.split(":")[1])
    await state.set_state(AdminEditProduct.choosing_field)
    await state.update_data(product_id=product_id)
    await call.message.edit_text(
        "✏️ Выберите поле для редактирования:",
        reply_markup=kb_admin_edit_fields(product_id)
    )
    await call.answer()


@router.callback_query(AdminEditProduct.choosing_field, F.data.startswith("adm_ef:"))
async def cb_adm_edit_field(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    product_id = int(parts[1])
    field = parts[2]
    await state.update_data(field=field, product_id=product_id)

    if field == "photos":
        await state.update_data(photos=[])
        await state.set_state(AdminEditProduct.entering_photos)
        await call.message.answer(
            "Отправьте новые фотографии (до 10), затем /done:",
            reply_markup=ReplyKeyboardRemove()
        )
    elif field == "category_id":
        categories = db_get_all_categories()
        await state.set_state(AdminEditProduct.entering_value)
        await call.message.answer(
            "Выберите новую категорию:",
            reply_markup=kb_select_category_for_product(categories)
        )
    else:
        prompts = {
            "name": "Введите новое название:",
            "description": "Введите новое описание:",
            "price": "Введите новую цену:",
            "old_price": "Введите старую цену (0 чтобы убрать):",
            "sizes": "Введите размеры через запятую:",
            "colors": "Введите цвета через запятую:",
        }
        await state.set_state(AdminEditProduct.entering_value)
        await call.message.answer(
            prompts.get(field, "Введите новое значение:"),
            reply_markup=ReplyKeyboardRemove()
        )
    await call.answer()


@router.message(AdminEditProduct.entering_photos, F.photo)
async def adm_edit_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    if len(photos) >= 10:
        await message.answer("⚠️ Максимум 10 фотографий. Отправьте /done")
        return
    file_id = message.photo[-1].file_id
    photos.append(file_id)
    await state.update_data(photos=photos)
    await message.answer(f"✅ Фото {len(photos)}/10 принято. Ещё или /done")


@router.message(AdminEditProduct.entering_photos, Command("done"))
async def adm_edit_photos_done(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data["product_id"]
    photos = data.get("photos", [])
    if not photos:
        await message.answer("⚠️ Добавьте хотя бы одно фото!")
        return
    db_update_product_field(product_id, "photos", photos)
    await state.clear()
    await message.answer(f"✅ Фото обновлены ({len(photos)} шт.).", reply_markup=kb_admin_main())


@router.callback_query(AdminEditProduct.entering_value, F.data.startswith("adm_prod_cat:"))
async def adm_edit_category(call: CallbackQuery, state: FSMContext):
    cat_id_str = call.data.split(":")[1]
    cat_id = int(cat_id_str) if cat_id_str != "0" else None
    data = await state.get_data()
    product_id = data["product_id"]
    db_update_product_field(product_id, "category_id", cat_id)
    await state.clear()
    await call.message.answer("✅ Категория обновлена.", reply_markup=kb_admin_main())
    await call.answer()


@router.message(AdminEditProduct.entering_value)
async def adm_edit_value(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data["product_id"]
    field = data["field"]

    if field == "price":
        try:
            value = float(message.text.strip().replace(",", "."))
        except ValueError:
            await message.answer("⚠️ Введите число:")
            return
    elif field == "old_price":
        try:
            v = float(message.text.strip().replace(",", "."))
            value = v if v > 0 else None
        except ValueError:
            await message.answer("⚠️ Введите число:")
            return
    elif field in ("sizes", "colors"):
        value = [s.strip() for s in message.text.split(",") if s.strip()]
    else:
        value = message.text.strip()

    db_update_product_field(product_id, field, value)
    await state.clear()
    await message.answer("✅ Поле обновлено.", reply_markup=kb_admin_main())


# ─────── ADMIN: STOCK ───────

@router.callback_query(F.data.startswith("adm_stock:"))
async def cb_adm_stock(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    product_id = int(call.data.split(":")[1])
    stock_rows = db_get_all_stock(product_id)
    product = db_get_product(product_id)

    if not stock_rows:
        stock_text = "нет данных"
    else:
        lines = []
        for row in stock_rows:
            emoji = "🟢" if row["stock"] >= 5 else ("🟡" if row["stock"] > 0 else "🔴")
            lines.append(f"{emoji} {row['size']} / {row['color']}: <b>{row['stock']} шт.</b>")
        stock_text = "\n".join(lines)

    await state.set_state(AdminEditProduct.entering_stock)
    await state.update_data(product_id=product_id)
    await call.message.answer(
        f"📦 <b>Остатки — {product['name']}</b>\n\n"
        f"{stock_text}\n\n"
        f"Введите новые остатки (формат: <code>размер,цвет,количество</code> — по одному на строку):"
    )
    await call.answer()


@router.message(AdminEditProduct.entering_stock)
async def adm_stock_input(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data["product_id"]
    errors = []
    updated = 0
    for line in message.text.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 3:
            size, color, qty_str = parts
            try:
                qty = int(qty_str)
                db_set_stock(product_id, size, color, qty)
                updated += 1
            except ValueError:
                errors.append(line)
        else:
            errors.append(line)

    if errors:
        await message.answer(
            f"⚠️ Ошибки в строках:\n<code>" + "\n".join(errors) + "</code>"
        )
    if updated > 0:
        await message.answer(f"✅ Обновлено {updated} позиций.", reply_markup=kb_admin_main())
    await state.clear()


# ─────── ADMIN: ORDERS ───────

@router.message(StateFilter(None), F.text == "📦 Заказы")
async def admin_orders(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    orders = db_get_all_orders()
    if not orders:
        await message.answer("📦 Заказов пока нет.")
        return

    counts = {"pending": 0, "paid": 0, "confirmed": 0, "rejected": 0}
    for o in orders:
        if o["status"] in counts:
            counts[o["status"]] += 1

    summary = (
        f"📦 <b>Все заказы</b> (всего: {len(orders)})\n\n"
        f"⏳ Ждут оплаты: {counts['pending']}\n"
        f"💳 Ждут подтверждения: {counts['paid']}\n"
        f"✅ Подтверждены: {counts['confirmed']}\n"
        f"❌ Отклонены: {counts['rejected']}"
    )
    await message.answer(summary, reply_markup=kb_admin_orders(orders))


@router.callback_query(F.data.startswith("adm_order:"))
async def cb_adm_order(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    order_id = int(call.data.split(":")[1])
    order = db_get_order(order_id)
    if not order:
        await call.answer("Заказ не найден")
        return

    items = json.loads(order["items"])
    items_text = format_order_items_text(items)
    promo_info = ""
    if order["promo_code"]:
        promo_info = f"\n🎟 Промокод: {order['promo_code']} (−{order['discount_amount']:.2f} ₽)"

    status_map = {
        "pending": "⏳ Ожидает оплаты",
        "paid": "💳 Оплачен, ждёт подтверждения",
        "confirmed": "✅ Подтверждён",
        "rejected": "❌ Отклонён",
    }
    status_str = status_map.get(order["status"], order["status"])

    user = db_get_user(order["tg_id"])
    username_str = f"@{user['username']}" if user and user["username"] else "—"

    text = (
        f"<b>Заказ #{order_id}</b> — {status_str}\n\n"
        f"👤 {order['name']}\n"
        f"🧑 {username_str}\n"
        f"🆔 <code>{order['tg_id']}</code>\n"
        f"📱 {order['phone']}\n"
        f"📍 {order['address']}\n\n"
        f"🛍 <b>Товары:</b>\n{items_text}"
        f"{promo_info}\n\n"
        f"💰 <b>Итого: {order['total']:.2f} ₽</b>\n"
        f"📅 {order['created_at'][:16]}"
    )

    kb = None
    if order["status"] == "paid":
        kb = kb_admin_order(order_id)

    await call.message.answer(text, reply_markup=kb)
    await call.answer()


# ─────── ADMIN: PROMOS ───────

@router.message(StateFilter(None), F.text == "🎟 Промокоды")
async def admin_promos(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    promos = db_get_all_promos()
    count = len(promos)
    await message.answer(
        f"🎟 <b>Промокоды</b>\n\nВсего: {count}",
        reply_markup=kb_admin_promos(promos)
    )


@router.callback_query(F.data == "adm_back_promos")
async def cb_adm_back_promos(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    promos = db_get_all_promos()
    await call.message.edit_text(
        f"🎟 <b>Промокоды</b>\n\nВсего: {len(promos)}",
        reply_markup=kb_admin_promos(promos)
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm_promo:"))
async def cb_adm_promo(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    promo_id = int(call.data.split(":")[1])
    conn = get_db()
    promo = conn.execute("SELECT * FROM promo_codes WHERE id=?", (promo_id,)).fetchone()
    conn.close()
    if not promo:
        await call.answer("Не найден")
        return
    disc = f"{promo['value']:.0f}%" if promo["type"] == "percent" else f"{promo['value']:.0f} ₽"
    status = "✅ Активен" if promo["is_active"] else "🚫 Отключён"
    text = (
        f"🎟 <b>{promo['code']}</b>\n\n"
        f"Тип: {'Процент' if promo['type'] == 'percent' else 'Фиксированная сумма'}\n"
        f"Скидка: −{disc}\n"
        f"Статус: {status}\n"
        f"Создан: {promo['created_at'][:10]}"
    )
    await call.message.edit_text(
        text, reply_markup=kb_admin_promo_actions(promo_id, promo["is_active"])
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm_promo_toggle:"))
async def cb_adm_promo_toggle(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    promo_id = int(call.data.split(":")[1])
    db_toggle_promo(promo_id)
    conn = get_db()
    promo = conn.execute("SELECT * FROM promo_codes WHERE id=?", (promo_id,)).fetchone()
    conn.close()
    await call.message.edit_reply_markup(
        reply_markup=kb_admin_promo_actions(promo_id, promo["is_active"])
    )
    await call.answer("Статус изменён")


@router.callback_query(F.data.startswith("adm_promo_del:"))
async def cb_adm_promo_del(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    promo_id = int(call.data.split(":")[1])
    db_delete_promo(promo_id)
    await call.message.edit_text("🗑 Промокод удалён.")
    await call.answer()


@router.callback_query(F.data == "adm_add_promo")
async def cb_adm_add_promo(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(AdminAddPromo.code)
    await call.message.answer(
        "🎟 <b>Новый промокод</b>\n\nВведите <b>код</b> промокода (будет в верхнем регистре):",
        reply_markup=ReplyKeyboardRemove()
    )
    await call.answer()


@router.message(AdminAddPromo.code)
async def adm_promo_code(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    existing = db_get_promo(code)
    if existing:
        await message.answer("⚠️ Такой промокод уже существует. Введите другой:")
        return
    await state.update_data(code=code)
    await state.set_state(AdminAddPromo.ptype)
    await message.answer(
        "Выберите <b>тип скидки</b>:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Процент (%)", callback_data="promo_type:percent"),
                InlineKeyboardButton(text="💰 Фиксированная (₽)", callback_data="promo_type:fixed"),
            ]
        ])
    )


@router.callback_query(AdminAddPromo.ptype, F.data.startswith("promo_type:"))
async def adm_promo_type(call: CallbackQuery, state: FSMContext):
    ptype = call.data.split(":")[1]
    await state.update_data(ptype=ptype)
    await state.set_state(AdminAddPromo.value)
    if ptype == "percent":
        label = "процент скидки (например: 15 для скидки 15%)"
    else:
        label = "сумму скидки в рублях (например: 500)"
    await call.message.answer(f"Введите {label}:")
    await call.answer()


@router.message(AdminAddPromo.value)
async def adm_promo_value(message: Message, state: FSMContext):
    try:
        value = float(message.text.strip().replace(",", "."))
        if value <= 0:
            raise ValueError
    except ValueError:
        await message.answer("⚠️ Введите положительное число:")
        return
    data = await state.get_data()
    db_add_promo(data["code"], data["ptype"], value)
    await state.clear()
    disc = f"{value:.0f}%" if data["ptype"] == "percent" else f"{value:.0f} ₽"
    await message.answer(
        f"✅ Промокод <b>{data['code']}</b> (скидка −{disc}) создан!",
        reply_markup=kb_admin_main()
    )


# ─────────────────────────────────────────────
# ADMIN: РАСШИРЕННЫЙ РАЗДЕЛ КЛИЕНТОВ
# ─────────────────────────────────────────────

@router.message(StateFilter(None), F.text == "👥 Клиенты")
async def admin_clients(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    users = db_get_all_users()
    banned = sum(1 for u in users if u["is_banned"])
    await message.answer(
        f"👥 <b>Управление клиентами</b>\n\n"
        f"Всего пользователей: <b>{len(users)}</b>\n"
        f"Забаненных: <b>{banned}</b>",
        reply_markup=kb_admin_clients_menu()
    )


@router.callback_query(F.data == "adm_back_clients")
async def cb_adm_back_clients(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    users = db_get_all_users()
    banned = sum(1 for u in users if u["is_banned"])
    await call.message.edit_text(
        f"👥 <b>Управление клиентами</b>\n\n"
        f"Всего пользователей: <b>{len(users)}</b>\n"
        f"Забаненных: <b>{banned}</b>",
        reply_markup=kb_admin_clients_menu()
    )
    await call.answer()


@router.callback_query(F.data.startswith("adm_clients_list:"))
async def cb_adm_clients_list(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    page = int(call.data.split(":")[1])
    users = db_get_all_users()
    page_size = 15
    total_pages = max(1, (len(users) + page_size - 1) // page_size)
    page = max(0, min(page, total_pages - 1))
    slice_users = users[page * page_size: (page + 1) * page_size]

    lines = [f"👥 <b>Клиенты</b> (стр. {page + 1}/{total_pages})\n"]
    for u in slice_users:
        uname = f"@{u['username']}" if u["username"] else "—"
        name = f"{u['first_name']} {u['last_name'] or ''}".strip() or "—"
        ban_icon = "🚫" if u["is_banned"] else ""
        lines.append(f"{ban_icon} {name} | {uname} | <code>{u['tg_id']}</code>")

    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="◀️", callback_data=f"adm_clients_list:{page - 1}"))
    if page < total_pages - 1:
        nav_buttons.append(InlineKeyboardButton(text="▶️", callback_data=f"adm_clients_list:{page + 1}"))

    # Кнопки для каждого юзера на странице
    user_buttons = []
    for u in slice_users:
        name = f"{u['first_name']} {u['last_name'] or ''}".strip() or "—"
        ban_icon = "🚫 " if u["is_banned"] else ""
        user_buttons.append([InlineKeyboardButton(
            text=f"{ban_icon}{name[:20]}",
            callback_data=f"adm_user:{u['tg_id']}"
        )])

    kb_rows = user_buttons
    if nav_buttons:
        kb_rows.append(nav_buttons)
    kb_rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="adm_back_clients")])

    text = "\n".join(lines)
    try:
        await call.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows))
    except Exception:
        await call.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows))
    await call.answer()


@router.callback_query(F.data == "adm_clients_banned")
async def cb_adm_clients_banned(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    users = [u for u in db_get_all_users() if u["is_banned"]]
    if not users:
        await call.answer("Забаненных пользователей нет", show_alert=True)
        return

    lines = [f"🚫 <b>Забаненные пользователи</b> ({len(users)})\n"]
    kb_rows = []
    for u in users:
        uname = f"@{u['username']}" if u["username"] else "—"
        name = f"{u['first_name']} {u['last_name'] or ''}".strip() or "—"
        lines.append(f"🚫 {name} | {uname} | <code>{u['tg_id']}</code>")
        kb_rows.append([InlineKeyboardButton(
            text=f"✅ Разбанить {name[:15]}",
            callback_data=f"adm_unban:{u['tg_id']}"
        )])

    kb_rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="adm_back_clients")])
    await call.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_rows)
    )
    await call.answer()


@router.callback_query(F.data == "adm_clients_search")
async def cb_adm_clients_search(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(AdminUserAction.waiting_search)
    await call.message.answer(
        "🔍 Введите <b>username</b> (без @) или <b>Telegram ID</b> пользователя:",
        reply_markup=ReplyKeyboardRemove()
    )
    await call.answer()


@router.message(AdminUserAction.waiting_search)
async def adm_user_search(message: Message, state: FSMContext):
    query = message.text.strip()
    conn = get_db()

    # Пробуем как ID
    user = None
    try:
        tg_id = int(query)
        user = conn.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)).fetchone()
    except ValueError:
        pass

    # Пробуем как username
    if not user:
        user = conn.execute(
            "SELECT * FROM users WHERE username=? COLLATE NOCASE", (query.lstrip("@"),)
        ).fetchone()

    conn.close()

    if not user:
        await state.clear()
        await message.answer(
            f"❌ Пользователь «{query}» не найден.",
            reply_markup=kb_admin_main()
        )
        return

    await state.clear()
    await show_admin_user_card(message, user)


async def show_admin_user_card(target, user):
    """Показывает карточку пользователя с действиями."""
    uname = f"@{user['username']}" if user["username"] else "—"
    name = f"{user['first_name']} {user['last_name'] or ''}".strip() or "—"
    ban_status = "🚫 Забанен" if user["is_banned"] else "✅ Активен"
    note = user["note"] or "—" if "note" in user.keys() else "—"

    # Считаем заказы
    conn = get_db()
    order_count = conn.execute("SELECT COUNT(*) FROM orders WHERE tg_id=?", (user["tg_id"],)).fetchone()[0]
    total_spent = conn.execute(
        "SELECT COALESCE(SUM(total),0) FROM orders WHERE tg_id=? AND status IN ('paid','confirmed')",
        (user["tg_id"],)
    ).fetchone()[0]
    conn.close()

    text = (
        f"👤 <b>Профиль пользователя</b>\n\n"
        f"Имя: {name}\n"
        f"Username: {uname}\n"
        f"Telegram ID: <code>{user['tg_id']}</code>\n"
        f"Язык: {user['lang']}\n"
        f"Статус: {ban_status}\n"
        f"Заметка: {note}\n\n"
        f"📦 Заказов: <b>{order_count}</b>\n"
        f"💰 Потрачено: <b>{total_spent:.2f} ₽</b>\n"
        f"📅 Зарегистрирован: {user['created_at'][:10]}"
    )

    if hasattr(target, "answer"):
        await target.answer(text, reply_markup=kb_admin_user_actions(user["tg_id"], user["is_banned"]))
    else:
        await target.message.answer(text, reply_markup=kb_admin_user_actions(user["tg_id"], user["is_banned"]))


@router.callback_query(F.data.startswith("adm_user:"))
async def cb_adm_user(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    tg_id = int(call.data.split(":")[1])
    user = db_get_user(tg_id)
    if not user:
        await call.answer("Пользователь не найден")
        return
    await call.answer()
    await show_admin_user_card(call, user)


@router.callback_query(F.data.startswith("adm_ban:"))
async def cb_adm_ban(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    tg_id = int(call.data.split(":")[1])
    db_ban_user(tg_id)
    await call.answer("Пользователь забанен")
    user = db_get_user(tg_id)
    if user:
        try:
            lang = user["lang"] or "ru"
            await bot.send_message(tg_id, t("banned_message", lang))
        except Exception:
            pass
    await call.message.edit_reply_markup(
        reply_markup=kb_admin_user_actions(tg_id, 1)
    )


@router.callback_query(F.data.startswith("adm_unban:"))
async def cb_adm_unban(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    tg_id = int(call.data.split(":")[1])
    db_unban_user(tg_id)
    await call.answer("Пользователь разбанен")
    try:
        await call.message.edit_reply_markup(
            reply_markup=kb_admin_user_actions(tg_id, 0)
        )
    except Exception:
        pass


@router.callback_query(F.data.startswith("adm_note:"))
async def cb_adm_note(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    tg_id = int(call.data.split(":")[1])
    await state.set_state(AdminUserAction.waiting_note)
    await state.update_data(target_tg_id=tg_id)
    await call.message.answer(
        "📝 Введите заметку для пользователя (или отправьте «-» чтобы очистить):",
        reply_markup=ReplyKeyboardRemove()
    )
    await call.answer()


@router.message(AdminUserAction.waiting_note)
async def adm_user_note_input(message: Message, state: FSMContext):
    data = await state.get_data()
    tg_id = data["target_tg_id"]
    note = message.text.strip()
    if note == "-":
        note = ""
    db_set_user_note(tg_id, note)
    await state.clear()
    await message.answer("✅ Заметка сохранена.", reply_markup=kb_admin_main())


@router.callback_query(F.data.startswith("adm_msg_user:"))
async def cb_adm_msg_user(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    tg_id = int(call.data.split(":")[1])
    await state.set_state(AdminUserAction.waiting_message)
    await state.update_data(target_tg_id=tg_id)
    await call.message.answer(
        "✉️ Введите сообщение, которое будет отправлено пользователю:",
        reply_markup=ReplyKeyboardRemove()
    )
    await call.answer()


@router.message(AdminUserAction.waiting_message)
async def adm_user_message_send(message: Message, state: FSMContext):
    data = await state.get_data()
    tg_id = data["target_tg_id"]
    await state.clear()
    try:
        await bot.send_message(tg_id, f"📩 <b>Сообщение от администратора:</b>\n\n{message.text}")
        await message.answer("✅ Сообщение отправлено.", reply_markup=kb_admin_main())
    except Exception:
        await message.answer("❌ Не удалось отправить сообщение (пользователь мог заблокировать бот).", reply_markup=kb_admin_main())


@router.callback_query(F.data.startswith("adm_user_orders:"))
async def cb_adm_user_orders(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    tg_id = int(call.data.split(":")[1])
    orders = db_get_user_orders(tg_id)
    user = db_get_user(tg_id)
    name = f"{user['first_name']} {user['last_name'] or ''}".strip() if user else str(tg_id)

    if not orders:
        await call.answer("У пользователя нет заказов", show_alert=True)
        return

    status_map = {
        "pending": "⏳", "paid": "💳", "confirmed": "✅", "rejected": "❌"
    }
    lines = [f"📦 <b>Заказы пользователя {name}</b>\n"]
    for o in orders[:15]:
        icon = status_map.get(o["status"], "❓")
        items = json.loads(o["items"])
        items_short = ", ".join(f"{i['name']} ×{i['quantity']}" for i in items[:2])
        lines.append(
            f"{icon} <b>#{o['id']}</b> — {o['total']:.0f} ₽\n"
            f"   {items_short}\n"
            f"   📅 {o['created_at'][:10]}"
        )

    await call.message.answer("\n".join(lines))
    await call.answer()


# ─────────────────────────────────────────────
# ADMIN: BROADCAST
# ─────────────────────────────────────────────

@router.message(StateFilter(None), F.text == "📢 Рассылка")
async def admin_broadcast_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    users = db_get_all_users()
    active_users = [u for u in users if not u["is_banned"]]
    await state.set_state(AdminBroadcast.message)
    await message.answer(
        f"📢 <b>Рассылка</b>\n\n"
        f"Получателей: {len(active_users)} чел. (активных)\n\n"
        f"Отправьте сообщение для рассылки (текст, фото с подписью или видео с подписью):",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(AdminBroadcast.message)
async def admin_broadcast_preview(message: Message, state: FSMContext):
    await state.update_data(
        text=message.text or message.caption or "",
        photo_id=message.photo[-1].file_id if message.photo else None,
        video_id=message.video.file_id if message.video else None,
    )
    await state.set_state(AdminBroadcast.confirm)
    users = [u for u in db_get_all_users() if not u["is_banned"]]
    await message.answer(
        f"📤 Подтвердите отправку рассылки <b>{len(users)}</b> пользователям:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_confirm"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="broadcast_cancel"),
            ]
        ])
    )


@router.callback_query(AdminBroadcast.confirm, F.data == "broadcast_confirm")
async def admin_broadcast_send(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    data = await state.get_data()
    await state.clear()
    users = [u for u in db_get_all_users() if not u["is_banned"]]
    sent = 0
    failed = 0

    await call.message.answer(f"⏳ Начинаю рассылку на {len(users)} пользователей...")
    await call.answer()

    for user in users:
        try:
            if data.get("photo_id"):
                await bot.send_photo(
                    chat_id=user["tg_id"],
                    photo=data["photo_id"],
                    caption=data["text"]
                )
            elif data.get("video_id"):
                await bot.send_video(
                    chat_id=user["tg_id"],
                    video=data["video_id"],
                    caption=data["text"]
                )
            else:
                await bot.send_message(
                    chat_id=user["tg_id"],
                    text=data["text"]
                )
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await call.message.answer(
        f"📢 <b>Рассылка завершена!</b>\n\n"
        f"✅ Доставлено: {sent}\n"
        f"❌ Ошибок: {failed}",
        reply_markup=kb_admin_main()
    )


@router.callback_query(AdminBroadcast.confirm, F.data == "broadcast_cancel")
async def admin_broadcast_cancel(call: CallbackQuery, state: FSMContext):
    await state.clear()
    await call.message.answer("❌ Рассылка отменена.", reply_markup=kb_admin_main())
    await call.answer()


# ─────────────────────────────────────────────
# ADMIN: STATISTICS (расширенная)
# ─────────────────────────────────────────────

@router.message(StateFilter(None), F.text == "📊 Статистика")
async def admin_stats(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    users_count, orders_count, revenue, pending_count, today_orders, products_count, banned_count, new_users_week = db_stats()
    is_maint = db_is_maintenance()
    maint_status = "🔴 Закрыт (тех. перерыв)" if is_maint else "🟢 Открыт"

    # Топ покупателей
    conn = get_db()
    top_buyers = conn.execute("""
        SELECT u.first_name, u.last_name, u.username, o.tg_id,
               COUNT(o.id) as cnt,
               SUM(o.total) as spent
        FROM orders o
        JOIN users u ON o.tg_id = u.tg_id
        WHERE o.status IN ('paid', 'confirmed')
        GROUP BY o.tg_id
        ORDER BY spent DESC
        LIMIT 5
    """).fetchall()

    # Популярные товары
    top_products = conn.execute("""
        SELECT p.name, SUM(json_extract(oi.value, '$.quantity')) as total_qty
        FROM orders o,
             json_each(o.items) oi
        JOIN products p ON json_extract(oi.value, '$.product_id') = p.id
        WHERE o.status IN ('paid', 'confirmed')
        GROUP BY json_extract(oi.value, '$.product_id')
        ORDER BY total_qty DESC
        LIMIT 5
    """).fetchall()
    conn.close()

    top_buyers_text = ""
    if top_buyers:
        lines = []
        for i, b in enumerate(top_buyers, 1):
            name = f"{b['first_name']} {b['last_name'] or ''}".strip() or "—"
            uname = f"@{b['username']}" if b["username"] else ""
            lines.append(f"{i}. {name} {uname} — {b['spent']:.0f} ₽ ({b['cnt']} зак.)")
        top_buyers_text = "\n\n🏆 <b>Топ покупателей:</b>\n" + "\n".join(lines)

    top_products_text = ""
    if top_products:
        lines = []
        for i, p in enumerate(top_products, 1):
            lines.append(f"{i}. {p['name']} — {p['total_qty']} шт.")
        top_products_text = "\n\n🔥 <b>Популярные товары:</b>\n" + "\n".join(lines)

    await message.answer(
        f"📊 <b>Статистика {SHOP_NAME}</b>\n\n"
        f"🏪 Статус магазина: {maint_status}\n\n"
        f"👥 Пользователей: <b>{users_count}</b>\n"
        f"🆕 Новых за неделю: <b>{new_users_week}</b>\n"
        f"🚫 Забаненных: <b>{banned_count}</b>\n"
        f"🛍 Активных товаров: <b>{products_count}</b>\n\n"
        f"📦 Всего заказов: <b>{orders_count}</b>\n"
        f"💳 Ждут подтверждения: <b>{pending_count}</b>\n"
        f"📅 Заказов сегодня: <b>{today_orders}</b>\n\n"
        f"💰 <b>Выручка (оплаченные): {revenue:.2f} ₽</b>"
        f"{top_buyers_text}"
        f"{top_products_text}"
    )


# ─────────────────────────────────────────────
# ADMIN: SETTINGS
# ─────────────────────────────────────────────

@router.message(StateFilter(None), F.text == "⚙️ Настройки")
async def admin_settings(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    payment_link = db_get_setting("payment_link") or DEFAULT_PAYMENT_LINK
    await message.answer(
        f"⚙️ <b>Настройки магазина</b>\n\n"
        f"💳 Ссылка оплаты:\n<code>{payment_link}</code>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить ссылку оплаты", callback_data="adm_set_paylink")]
        ])
    )


@router.callback_query(F.data == "adm_set_paylink")
async def cb_adm_set_paylink(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(AdminSetPayLink.link)
    await call.message.answer(
        "Введите новую ссылку для оплаты:\n<i>(должна начинаться с https://)</i>",
        reply_markup=ReplyKeyboardRemove()
    )
    await call.answer()


@router.message(AdminSetPayLink.link)
async def adm_set_paylink(message: Message, state: FSMContext):
    link = message.text.strip()
    if not link.startswith("http"):
        await message.answer("⚠️ Ссылка должна начинаться с http:// или https://")
        return
    db_set_setting("payment_link", link)
    await state.clear()
    await message.answer(
        f"✅ Ссылка оплаты обновлена:\n<code>{link}</code>",
        reply_markup=kb_admin_main()
    )


# ─────── NOOP ───────

@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    await call.answer()


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

async def main():
    init_db()
    logger.info(f"Starting {SHOP_NAME} bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
