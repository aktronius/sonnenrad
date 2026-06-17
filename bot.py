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

BOT_TOKEN = "8739516166:AAGVEq4oeNb42aY-uDY1vCMOj9mNhsvucmI"  # <-- Вставь токен сюда

ADMIN_IDS = [7752932648, 8379783147]

DB_PATH = "sonnenrad.db"

SHOP_NAME = "Sonnenrad"

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
    "welcome": {
        "ru": f"☀️ Добро пожаловать в {SHOP_NAME}!\n\nВыберите язык:",
        "uk": f"☀️ Ласкаво просимо до {SHOP_NAME}!\n\nОберіть мову:",
        "en": f"☀️ Welcome to {SHOP_NAME}!\n\nChoose your language:",
        "no": f"☀️ Velkommen til {SHOP_NAME}!\n\nVelg språk:",
        "sv": f"☀️ Välkommen till {SHOP_NAME}!\n\nVälj språk:",
    },
    "language_saved": {
        "ru": "✅ Язык сохранён. Добро пожаловать!",
        "uk": "✅ Мову збережено. Ласкаво просимо!",
        "en": "✅ Language saved. Welcome!",
        "no": "✅ Språk lagret. Velkommen!",
        "sv": "✅ Språk sparat. Välkommen!",
    },
    "main_menu": {
        "ru": "🏠 Главное меню",
        "uk": "🏠 Головне меню",
        "en": "🏠 Main Menu",
        "no": "🏠 Hovedmeny",
        "sv": "🏠 Huvudmeny",
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
    "catalog_empty": {
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
        "ru": "✅ Товар добавлен в корзину!",
        "uk": "✅ Товар додано до кошика!",
        "en": "✅ Item added to cart!",
        "no": "✅ Vare lagt til i handlekurven!",
        "sv": "✅ Vara tillagd i varukorgen!",
    },
    "cart_empty": {
        "ru": "🛒 Корзина пуста.",
        "uk": "🛒 Кошик порожній.",
        "en": "🛒 Your cart is empty.",
        "no": "🛒 Handlekurven er tom.",
        "sv": "🛒 Varukorgen är tom.",
    },
    "cart_total": {
        "ru": "💰 Итого: {total} ₽",
        "uk": "💰 Разом: {total} ₽",
        "en": "💰 Total: {total} ₽",
        "no": "💰 Totalt: {total} ₽",
        "sv": "💰 Totalt: {total} ₽",
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
        "ru": "👤 Введите ваше имя:",
        "uk": "👤 Введіть ваше ім'я:",
        "en": "👤 Enter your name:",
        "no": "👤 Skriv inn navnet ditt:",
        "sv": "👤 Ange ditt namn:",
    },
    "enter_phone": {
        "ru": "📱 Введите номер телефона:",
        "uk": "📱 Введіть номер телефону:",
        "en": "📱 Enter your phone number:",
        "no": "📱 Skriv inn telefonnummeret ditt:",
        "sv": "📱 Ange ditt telefonnummer:",
    },
    "enter_address": {
        "ru": "📍 Введите адрес доставки:",
        "uk": "📍 Введіть адресу доставки:",
        "en": "📍 Enter delivery address:",
        "no": "📍 Skriv inn leveringsadressen:",
        "sv": "📍 Ange leveransadressen:",
    },
    "enter_promo": {
        "ru": "🎟 Введите промокод (или нажмите «Пропустить»):",
        "uk": "🎟 Введіть промокод (або натисніть «Пропустити»):",
        "en": "🎟 Enter promo code (or press 'Skip'):",
        "no": "🎟 Skriv inn kampanjekode (eller trykk 'Hopp over'):",
        "sv": "🎟 Ange kampanjkod (eller tryck 'Hoppa över'):",
    },
    "skip": {
        "ru": "⏩ Пропустить",
        "uk": "⏩ Пропустити",
        "en": "⏩ Skip",
        "no": "⏩ Hopp over",
        "sv": "⏩ Hoppa över",
    },
    "promo_applied": {
        "ru": "✅ Промокод применён! Скидка: {discount}",
        "uk": "✅ Промокод застосовано! Знижка: {discount}",
        "en": "✅ Promo code applied! Discount: {discount}",
        "no": "✅ Kampanjekode brukt! Rabatt: {discount}",
        "sv": "✅ Kampanjkod tillämpad! Rabatt: {discount}",
    },
    "promo_invalid": {
        "ru": "❌ Неверный или неактивный промокод.",
        "uk": "❌ Невірний або неактивний промокод.",
        "en": "❌ Invalid or inactive promo code.",
        "no": "❌ Ugyldig eller inaktiv kampanjekode.",
        "sv": "❌ Ogiltig eller inaktiv kampanjkod.",
    },
    "order_confirm": {
        "ru": "📋 Подтверждение заказа:\n\n{items}\n\n👤 Имя: {name}\n📱 Телефон: {phone}\n📍 Адрес: {address}\n{promo_line}\n💰 Итого: {total} ₽\n\nПодтвердить заказ?",
        "uk": "📋 Підтвердження замовлення:\n\n{items}\n\n👤 Ім'я: {name}\n📱 Телефон: {phone}\n📍 Адреса: {address}\n{promo_line}\n💰 Разом: {total} ₽\n\nПідтвердити замовлення?",
        "en": "📋 Order Confirmation:\n\n{items}\n\n👤 Name: {name}\n📱 Phone: {phone}\n📍 Address: {address}\n{promo_line}\n💰 Total: {total} ₽\n\nConfirm order?",
        "no": "📋 Ordrebekreftelse:\n\n{items}\n\n👤 Navn: {name}\n📱 Telefon: {phone}\n📍 Adresse: {address}\n{promo_line}\n💰 Totalt: {total} ₽\n\nBekreft bestilling?",
        "sv": "📋 Orderbekräftelse:\n\n{items}\n\n👤 Namn: {name}\n📱 Telefon: {phone}\n📍 Adress: {address}\n{promo_line}\n💰 Totalt: {total} ₽\n\nBekräfta beställning?",
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
        "ru": "🎉 Заказ #{order_id} оформлен!\n\nНажмите кнопку ниже для оплаты:",
        "uk": "🎉 Замовлення #{order_id} оформлено!\n\nНатисніть кнопку нижче для оплати:",
        "en": "🎉 Order #{order_id} placed!\n\nClick the button below to pay:",
        "no": "🎉 Bestilling #{order_id} er lagt inn!\n\nKlikk på knappen nedenfor for å betale:",
        "sv": "🎉 Beställning #{order_id} lagd!\n\nKlicka på knappen nedan för att betala:",
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
        "ru": "⏳ Ожидайте подтверждения оплаты от администратора.",
        "uk": "⏳ Очікуйте підтвердження оплати від адміністратора.",
        "en": "⏳ Awaiting payment confirmation from administrator.",
        "no": "⏳ Venter på betalingsbekreftelse fra administrator.",
        "sv": "⏳ Väntar på betalningsbekräftelse från administratören.",
    },
    "order_approved": {
        "ru": "✅ Ваш заказ #{order_id} подтверждён! Спасибо за покупку.",
        "uk": "✅ Ваше замовлення #{order_id} підтверджено! Дякуємо за покупку.",
        "en": "✅ Your order #{order_id} has been confirmed! Thank you for your purchase.",
        "no": "✅ Bestillingen #{order_id} er bekreftet! Takk for kjøpet.",
        "sv": "✅ Din beställning #{order_id} har bekräftats! Tack för ditt köp.",
    },
    "order_rejected": {
        "ru": "❌ Ваш заказ #{order_id} был отклонён. Свяжитесь с поддержкой.",
        "uk": "❌ Ваше замовлення #{order_id} було відхилено. Зверніться до підтримки.",
        "en": "❌ Your order #{order_id} has been rejected. Please contact support.",
        "no": "❌ Bestillingen #{order_id} ble avvist. Kontakt støtte.",
        "sv": "❌ Din beställning #{order_id} har avvisats. Kontakta support.",
    },
    "no_orders": {
        "ru": "📦 У вас нет заказов.",
        "uk": "📦 У вас немає замовлень.",
        "en": "📦 You have no orders.",
        "no": "📦 Du har ingen bestillinger.",
        "sv": "📦 Du har inga beställningar.",
    },
    "order_status_pending": {
        "ru": "⏳ Ожидает оплаты",
        "uk": "⏳ Очікує оплати",
        "en": "⏳ Pending Payment",
        "no": "⏳ Venter på betaling",
        "sv": "⏳ Väntar på betalning",
    },
    "order_status_paid": {
        "ru": "✅ Оплачен",
        "uk": "✅ Оплачено",
        "en": "✅ Paid",
        "no": "✅ Betalt",
        "sv": "✅ Betald",
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
    "out_of_stock": {
        "ru": "❌ Нет в наличии",
        "uk": "❌ Немає в наявності",
        "en": "❌ Out of Stock",
        "no": "❌ Ikke på lager",
        "sv": "❌ Slut i lager",
    },
    "quantity": {
        "ru": "Кол-во",
        "uk": "Кількість",
        "en": "Qty",
        "no": "Antall",
        "sv": "Antal",
    },
    "remove": {
        "ru": "🗑 Удалить",
        "uk": "🗑 Видалити",
        "en": "🗑 Remove",
        "no": "🗑 Fjern",
        "sv": "🗑 Ta bort",
    },
    "promo_label": {
        "ru": "🎟 Промокод: {code} (-{discount})",
        "uk": "🎟 Промокод: {code} (-{discount})",
        "en": "🎟 Promo: {code} (-{discount})",
        "no": "🎟 Kampanje: {code} (-{discount})",
        "sv": "🎟 Kampanj: {code} (-{discount})",
    },
    "old_price": {
        "ru": "~~{old_price} ₽~~",
        "uk": "~~{old_price} ₽~~",
        "en": "~~{old_price} ₽~~",
        "no": "~~{old_price} ₽~~",
        "sv": "~~{old_price} ₽~~",
    },
    "page": {
        "ru": "Стр. {page}/{total}",
        "uk": "Стор. {page}/{total}",
        "en": "Page {page}/{total}",
        "no": "Side {page}/{total}",
        "sv": "Sida {page}/{total}",
    },
    "prev": {
        "ru": "◀️",
        "uk": "◀️",
        "en": "◀️",
        "no": "◀️",
        "sv": "◀️",
    },
    "next": {
        "ru": "▶️",
        "uk": "▶️",
        "en": "▶️",
        "no": "▶️",
        "sv": "▶️",
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
        created_at TEXT DEFAULT (datetime('now'))
    );

    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        old_price REAL,
        photos TEXT DEFAULT '[]',
        sizes TEXT DEFAULT '[]',
        colors TEXT DEFAULT '[]',
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
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

    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('payment_link', 'https://www.tinkoff.ru/rm/r_UJBvvZLldj.sElFsijULP/egIp160996')")
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


def db_get_active_products(page: int = 0, per_page: int = 5):
    conn = get_db()
    offset = page * per_page
    rows = conn.execute(
        "SELECT * FROM products WHERE is_active=1 ORDER BY id DESC LIMIT ? OFFSET ?",
        (per_page, offset)
    ).fetchall()
    total = conn.execute("SELECT COUNT(*) FROM products WHERE is_active=1").fetchone()[0]
    conn.close()
    return rows, total


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
    rows = conn.execute("SELECT * FROM users").fetchall()
    conn.close()
    return rows


def db_get_all_orders():
    conn = get_db()
    rows = conn.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
    conn.close()
    return rows


def db_get_all_products():
    conn = get_db()
    rows = conn.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    conn.close()
    return rows


def db_get_all_promos():
    conn = get_db()
    rows = conn.execute("SELECT * FROM promo_codes ORDER BY id DESC").fetchall()
    conn.close()
    return rows


def db_add_product(name, description, price, old_price, photos, sizes, colors):
    conn = get_db()
    cur = conn.execute("""
        INSERT INTO products (name, description, price, old_price, photos, sizes, colors)
        VALUES (?,?,?,?,?,?,?)
    """, (name, description, price, old_price,
          json.dumps(photos), json.dumps(sizes), json.dumps(colors)))
    product_id = cur.lastrowid
    conn.commit()
    conn.close()
    return product_id


def db_update_product_field(product_id: int, field: str, value):
    allowed = {"name", "description", "price", "old_price", "photos", "sizes", "colors", "is_active"}
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
    popular = conn.execute("""
        SELECT p.name, COUNT(*) as cnt FROM orders o
        JOIN products p ON json_extract(o.items, '$[0].product_id') = p.id
        GROUP BY p.id ORDER BY cnt DESC LIMIT 5
    """).fetchall()
    conn.close()
    return users_count, orders_count, revenue, popular


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


class AdminAddProduct(StatesGroup):
    name = State()
    description = State()
    price = State()
    old_price = State()
    photos = State()
    sizes = State()
    colors = State()
    stock = State()


class AdminEditProduct(StatesGroup):
    choosing_field = State()
    entering_value = State()
    entering_stock = State()


class AdminAddPromo(StatesGroup):
    code = State()
    ptype = State()
    value = State()


class AdminBroadcast(StatesGroup):
    message = State()


class AdminSetPayLink(StatesGroup):
    link = State()


class AdminEditPrice(StatesGroup):
    price = State()


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


def kb_catalog_item(product_id: int, lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("add_to_cart", lang), callback_data=f"buy:{product_id}")]
    ])


def kb_catalog_nav(page: int, total_pages: int, lang: str) -> InlineKeyboardMarkup:
    row = []
    if page > 0:
        row.append(InlineKeyboardButton(text=t("prev", lang), callback_data=f"cat_page:{page-1}"))
    row.append(InlineKeyboardButton(
        text=t("page", lang, page=page+1, total=total_pages), callback_data="noop"
    ))
    if page < total_pages - 1:
        row.append(InlineKeyboardButton(text=t("next", lang), callback_data=f"cat_page:{page+1}"))
    return InlineKeyboardMarkup(inline_keyboard=[row])


def kb_sizes(sizes: list, product_id: int) -> InlineKeyboardMarkup:
    rows = []
    row = []
    for i, size in enumerate(sizes):
        row.append(InlineKeyboardButton(text=size, callback_data=f"size:{product_id}:{size}"))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_colors(colors: list, product_id: int, size: str) -> InlineKeyboardMarkup:
    rows = []
    row = []
    for color in colors:
        row.append(InlineKeyboardButton(
            text=color, callback_data=f"color:{product_id}:{size}:{color}"
        ))
        if len(row) == 3:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_cart(cart_items, lang: str) -> InlineKeyboardMarkup:
    rows = []
    for item in cart_items:
        rows.append([
            InlineKeyboardButton(text="➖", callback_data=f"cart_dec:{item['id']}"),
            InlineKeyboardButton(
                text=f"{item['name']} {item['size']} {item['color']} x{item['quantity']}",
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
            [KeyboardButton(text="🛍 Товары"), KeyboardButton(text="📦 Заказы")],
            [KeyboardButton(text="🎟 Промокоды"), KeyboardButton(text="👥 Клиенты")],
            [KeyboardButton(text="📢 Рассылка"), KeyboardButton(text="📊 Статистика")],
            [KeyboardButton(text="⚙️ Настройки"), KeyboardButton(text="🏠 Выход")],
        ],
        resize_keyboard=True
    )


def kb_admin_products(products) -> InlineKeyboardMarkup:
    rows = []
    for p in products:
        status = "✅" if p["is_active"] else "❌"
        rows.append([InlineKeyboardButton(
            text=f"{status} {p['name']} — {p['price']}₽",
            callback_data=f"adm_prod:{p['id']}"
        )])
    rows.append([InlineKeyboardButton(text="➕ Добавить товар", callback_data="adm_add_product")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_admin_product_actions(product_id: int, is_active: int) -> InlineKeyboardMarkup:
    toggle_text = "🙈 Скрыть" if is_active else "👁 Показать"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить", callback_data=f"adm_edit:{product_id}")],
        [InlineKeyboardButton(text="📦 Остатки", callback_data=f"adm_stock:{product_id}")],
        [InlineKeyboardButton(text=toggle_text, callback_data=f"adm_toggle:{product_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"adm_del:{product_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="adm_back_products")],
    ])


def kb_admin_edit_fields(product_id: int) -> InlineKeyboardMarkup:
    fields = [
        ("Название", "name"), ("Описание", "description"),
        ("Цена", "price"), ("Старая цена", "old_price"),
        ("Размеры", "sizes"), ("Цвета", "colors"),
        ("Фото", "photos"),
    ]
    rows = [[InlineKeyboardButton(text=label, callback_data=f"adm_ef:{product_id}:{field}")]
            for label, field in fields]
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=f"adm_prod:{product_id}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_admin_promos(promos) -> InlineKeyboardMarkup:
    rows = []
    for p in promos:
        status = "✅" if p["is_active"] else "❌"
        disc = f"{p['value']}%" if p["type"] == "percent" else f"{p['value']}₽"
        rows.append([
            InlineKeyboardButton(
                text=f"{status} {p['code']} -{disc}",
                callback_data=f"adm_promo:{p['id']}"
            )
        ])
    rows.append([InlineKeyboardButton(text="➕ Добавить промокод", callback_data="adm_add_promo")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def kb_admin_promo_actions(promo_id: int, is_active: int) -> InlineKeyboardMarkup:
    toggle_text = "🔴 Выключить" if is_active else "🟢 Включить"
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
            text=f"{icon} #{o['id']} {o['name']} — {o['total']}₽",
            callback_data=f"adm_order:{o['id']}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=rows)


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
        lines.append(f"• {i['name']} | {i['size']} | {i['color']} x{i['quantity']} — {i['price'] * i['quantity']:.2f}₽")
    return "\n".join(lines)


def apply_discount(total: float, promo: sqlite3.Row) -> tuple:
    if promo["type"] == "percent":
        discount = round(total * promo["value"] / 100, 2)
        discount_str = f"{promo['value']}%"
    else:
        discount = min(promo["value"], total)
        discount_str = f"{promo['value']}₽"
    return discount, discount_str


def is_admin(tg_id: int) -> bool:
    return tg_id in ADMIN_IDS


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
    user = db_get_user(tg_id)

    db_upsert_user(
        tg_id,
        message.from_user.username or "",
        message.from_user.first_name or "",
        message.from_user.last_name or "",
    )

    if not user or not user["lang"]:
        await state.set_state(LangState.choosing)
        await message.answer(
            T["welcome"]["ru"],
            reply_markup=kb_lang_select()
        )
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
    await call.message.edit_reply_markup()
    await call.message.answer(
        t("language_saved", lang),
        reply_markup=kb_main_menu(lang)
    )
    await call.answer()


# ─────── CATALOG ───────

@router.message(F.text.in_([v for v in [
    T["catalog"].get(l) for l in LANGUAGES
] if v]))
async def handle_catalog(message: Message, state: FSMContext):
    await state.clear()
    lang = db_get_lang(message.from_user.id)
    await show_catalog_page(message, lang, 0)


async def show_catalog_page(message: Message, lang: str, page: int):
    products, total = db_get_active_products(page=page, per_page=5)
    if not products:
        await message.answer(t("catalog_empty", lang))
        return

    total_pages = (total + 4) // 5

    for product in products:
        photos = json.loads(product["photos"])
        sizes = json.loads(product["sizes"])
        colors = json.loads(product["colors"])

        old_price_text = ""
        if product["old_price"]:
            old_price_text = f"\n<s>{product['old_price']} ₽</s>"

        caption = (
            f"<b>{product['name']}</b>\n"
            f"{product['description'] or ''}\n"
            f"{old_price_text}"
            f"\n<b>{product['price']} ₽</b>\n"
            f"📐 {', '.join(sizes)}\n"
            f"🎨 {', '.join(colors)}"
        )

        kb = kb_catalog_item(product["id"], lang)

        if photos:
            media = [InputMediaPhoto(media=photo_id) for photo_id in photos[:10]]
            if len(media) == 1:
                await message.answer_photo(
                    photo=media[0].media,
                    caption=caption,
                    reply_markup=kb
                )
            else:
                media[0] = InputMediaPhoto(media=media[0].media, caption=caption)
                await message.answer_media_group(media=media)
                await message.answer(t("add_to_cart", lang), reply_markup=kb)
        else:
            await message.answer(caption, reply_markup=kb)

    if total_pages > 1:
        await message.answer(
            t("page", lang, page=page+1, total=total_pages),
            reply_markup=kb_catalog_nav(page, total_pages, lang)
        )


@router.callback_query(F.data.startswith("cat_page:"))
async def cb_catalog_page(call: CallbackQuery):
    page = int(call.data.split(":")[1])
    lang = db_get_lang(call.from_user.id)
    await call.message.delete()
    await show_catalog_page(call.message, lang, page)
    await call.answer()


@router.callback_query(F.data.startswith("buy:"))
async def cb_buy(call: CallbackQuery, state: FSMContext):
    product_id = int(call.data.split(":")[1])
    lang = db_get_lang(call.from_user.id)
    product = db_get_product(product_id)
    if not product:
        await call.answer("Товар не найден")
        return

    sizes = json.loads(product["sizes"])
    if not sizes:
        await call.answer("Нет доступных размеров")
        return

    await state.set_state(ProductState.selecting_size)
    await state.update_data(product_id=product_id)
    await call.message.answer(
        t("select_size", lang),
        reply_markup=kb_sizes(sizes, product_id)
    )
    await call.answer()


@router.callback_query(ProductState.selecting_size, F.data.startswith("size:"))
async def cb_select_size(call: CallbackQuery, state: FSMContext):
    _, product_id, size = call.data.split(":")
    product_id = int(product_id)
    lang = db_get_lang(call.from_user.id)
    product = db_get_product(product_id)
    if not product:
        await call.answer()
        return

    colors = json.loads(product["colors"])
    await state.update_data(size=size)
    await state.set_state(ProductState.selecting_color)
    await call.message.answer(
        t("select_color", lang),
        reply_markup=kb_colors(colors, product_id, size)
    )
    await call.answer()


@router.callback_query(ProductState.selecting_color, F.data.startswith("color:"))
async def cb_select_color(call: CallbackQuery, state: FSMContext):
    parts = call.data.split(":")
    product_id = int(parts[1])
    size = parts[2]
    color = parts[3]
    tg_id = call.from_user.id
    lang = db_get_lang(tg_id)

    stock = db_get_stock(product_id, size, color)
    if stock <= 0:
        await call.answer(t("out_of_stock", lang), show_alert=True)
        return

    db_add_to_cart(tg_id, product_id, size, color)
    await state.clear()
    await call.message.answer(
        t("added_to_cart", lang),
        reply_markup=kb_main_menu(lang)
    )
    await call.answer()


# ─────── CART ───────

@router.message(F.text.in_([v for v in [
    T["cart"].get(l) for l in LANGUAGES
] if v]))
async def handle_cart(message: Message, state: FSMContext):
    await state.clear()
    tg_id = message.from_user.id
    lang = db_get_lang(tg_id)
    cart = db_get_cart(tg_id)

    if not cart:
        await message.answer(t("cart_empty", lang))
        return

    total = calc_cart_total(cart)
    text = t("cart_total", lang, total=f"{total:.2f}")
    await message.answer(text, reply_markup=kb_cart(cart, lang))


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
    total = calc_cart_total(cart)
    await call.message.edit_text(
        t("cart_total", lang, total=f"{total:.2f}"),
        reply_markup=kb_cart(cart, lang)
    )
    await call.answer()


@router.callback_query(F.data.startswith("cart_inc:"))
async def cb_cart_inc(call: CallbackQuery):
    cart_id = int(call.data.split(":")[1])
    conn = get_db()
    row = conn.execute("SELECT quantity, product_id, size, color FROM cart WHERE id=?", (cart_id,)).fetchone()
    conn.close()
    if row:
        stock = db_get_stock(row["product_id"], row["size"], row["color"])
        lang = db_get_lang(call.from_user.id)
        if row["quantity"] >= stock:
            await call.answer(t("out_of_stock", lang), show_alert=True)
            return
        db_update_cart_qty(cart_id, row["quantity"] + 1)
    lang = db_get_lang(call.from_user.id)
    cart = db_get_cart(call.from_user.id)
    total = calc_cart_total(cart)
    await call.message.edit_text(
        t("cart_total", lang, total=f"{total:.2f}"),
        reply_markup=kb_cart(cart, lang)
    )
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
    total = calc_cart_total(cart)
    await call.message.edit_text(
        t("cart_total", lang, total=f"{total:.2f}"),
        reply_markup=kb_cart(cart, lang)
    )
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
            await message.answer(t("promo_invalid", lang))
            return

    await state.update_data(promo_code=promo_code, discount_amount=discount_amount, discount_str=discount_str)
    data = await state.get_data()
    tg_id = message.from_user.id
    cart = db_get_cart(tg_id)
    total_raw = calc_cart_total(cart)
    total = max(0.0, total_raw - discount_amount)

    items_text = format_order_items_text(format_items_for_order(cart))
    promo_line = ""
    if promo_code:
        promo_line = f"🎟 {promo_code} (-{discount_str})\n"

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
    await message.answer(confirm_text, reply_markup=kb_confirm_order(lang))


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

    payment_link = db_get_setting("payment_link") or "https://payment.example.com"

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

    db_set_order_status(order_id, "paid")

    items = json.loads(order["items"])

    for item in items:
        new_stock = db_decrement_stock(item["product_id"], item["size"], item["color"], item["quantity"])
        if new_stock < 3:
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(
                        admin_id,
                        f"⚠️ <b>Мало товара на складе!</b>\n"
                        f"Товар: {item['name']}\n"
                        f"Размер: {item['size']} | Цвет: {item['color']}\n"
                        f"Остаток: {new_stock} шт."
                    )
                except Exception:
                    pass

    user = db_get_user(tg_id)
    username = f"@{user['username']}" if user and user["username"] else "—"

    items_text = format_order_items_text(items)
    promo_info = f"\n🎟 Промокод: {order['promo_code']} (-{order['discount_amount']}₽)" if order["promo_code"] else ""

    admin_text = (
        f"🛒 <b>Новый оплаченный заказ #{order_id}</b>\n\n"
        f"👤 Имя: {order['name']}\n"
        f"🧑 Username: {username}\n"
        f"🆔 Telegram ID: {tg_id}\n"
        f"📱 Телефон: {order['phone']}\n"
        f"📍 Адрес: {order['address']}\n\n"
        f"🛍 Товары:\n{items_text}"
        f"{promo_info}\n\n"
        f"💰 Итого: {order['total']:.2f}₽"
    )

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(
                admin_id,
                admin_text,
                reply_markup=kb_admin_order(order_id)
            )
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
    db_set_order_status(order_id, "confirmed")
    await call.message.edit_reply_markup()
    await call.message.answer(f"✅ Заказ #{order_id} подтверждён.")
    lang = db_get_lang(order["tg_id"])
    try:
        await bot.send_message(
            order["tg_id"],
            t("order_approved", lang, order_id=order_id)
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
    db_set_order_status(order_id, "rejected")
    await call.message.edit_reply_markup()
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


# ─────── MY ORDERS ───────

@router.message(F.text.in_([v for v in [
    T["my_orders"].get(l) for l in LANGUAGES
] if v]))
async def handle_my_orders(message: Message, state: FSMContext):
    await state.clear()
    tg_id = message.from_user.id
    lang = db_get_lang(tg_id)
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

    text = ""
    for o in orders[:10]:
        status = status_map.get(o["status"], o["status"])
        items = json.loads(o["items"])
        items_short = ", ".join(f"{i['name']} x{i['quantity']}" for i in items)
        text += (
            f"📦 <b>Заказ #{o['id']}</b>\n"
            f"{status}\n"
            f"{items_short}\n"
            f"💰 {o['total']:.2f}₽\n"
            f"📅 {o['created_at'][:10]}\n\n"
        )

    await message.answer(text)


# ─────── SETTINGS ───────

@router.message(F.text.in_([v for v in [
    T["settings"].get(l) for l in LANGUAGES
] if v]))
async def handle_settings(message: Message, state: FSMContext):
    await state.clear()
    lang = db_get_lang(message.from_user.id)
    await message.answer(
        t("settings", lang),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("change_language", lang), callback_data="change_lang")]
        ])
    )


@router.callback_query(F.data == "change_lang")
async def cb_change_lang(call: CallbackQuery, state: FSMContext):
    await state.set_state(LangState.choosing)
    await call.message.answer(T["welcome"]["ru"], reply_markup=kb_lang_select())
    await call.answer()


# ─────────────────────────────────────────────
# ADMIN HANDLERS
# ─────────────────────────────────────────────

@router.message(Command("admin"))
async def cmd_admin(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await state.clear()
    await message.answer(
        f"🛡 <b>Панель администратора {SHOP_NAME}</b>",
        reply_markup=kb_admin_main()
    )


@router.message(F.text == "🏠 Выход", F.func(lambda m: is_admin(m.from_user.id)))
async def admin_exit(message: Message, state: FSMContext):
    await state.clear()
    lang = db_get_lang(message.from_user.id)
    await message.answer(t("main_menu", lang), reply_markup=kb_main_menu(lang))


# ─────── ADMIN: PRODUCTS ───────

@router.message(F.text == "🛍 Товары", F.func(lambda m: is_admin(m.from_user.id)))
async def admin_products(message: Message, state: FSMContext):
    await state.clear()
    products = db_get_all_products()
    await message.answer(
        "🛍 <b>Управление товарами</b>",
        reply_markup=kb_admin_products(products)
    )


@router.callback_query(F.data == "adm_back_products")
async def cb_adm_back_products(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    products = db_get_all_products()
    await call.message.edit_text(
        "🛍 <b>Управление товарами</b>",
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
    status = "✅ Активен" if product["is_active"] else "❌ Скрыт"
    text = (
        f"<b>{product['name']}</b>\n"
        f"{product['description'] or ''}\n\n"
        f"💰 Цена: {product['price']} ₽"
        + (f" | Старая: {product['old_price']} ₽" if product["old_price"] else "") + "\n"
        f"📐 Размеры: {', '.join(sizes)}\n"
        f"🎨 Цвета: {', '.join(colors)}\n"
        f"🖼 Фото: {len(photos)}\n"
        f"Статус: {status}"
    )
    await call.message.edit_text(text, reply_markup=kb_admin_product_actions(product_id, product["is_active"]))
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


@router.callback_query(F.data == "adm_add_product")
async def cb_adm_add_product(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(AdminAddProduct.name)
    await call.message.answer("Введите <b>название</b> товара:", reply_markup=ReplyKeyboardRemove())
    await call.answer()


@router.message(AdminAddProduct.name)
async def adm_product_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await state.set_state(AdminAddProduct.description)
    await message.answer("Введите <b>описание</b> товара:")


@router.message(AdminAddProduct.description)
async def adm_product_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text.strip())
    await state.set_state(AdminAddProduct.price)
    await message.answer("Введите <b>цену</b> (например: 49.99):")


@router.message(AdminAddProduct.price)
async def adm_product_price(message: Message, state: FSMContext):
    try:
        price = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("Неверный формат цены. Введите число:")
        return
    await state.update_data(price=price)
    await state.set_state(AdminAddProduct.old_price)
    await message.answer("Введите <b>старую цену</b> (или отправьте 0 чтобы пропустить):")


@router.message(AdminAddProduct.old_price)
async def adm_product_old_price(message: Message, state: FSMContext):
    try:
        old_price = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("Неверный формат цены:")
        return
    await state.update_data(old_price=old_price if old_price > 0 else None)
    await state.set_state(AdminAddProduct.photos)
    await message.answer(
        "Отправьте фотографии товара (до 10 штук).\n"
        "Когда закончите, отправьте команду <code>/done</code>"
    )
    await state.update_data(photos=[])


@router.message(AdminAddProduct.photos, F.photo)
async def adm_product_photo(message: Message, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    if len(photos) >= 10:
        await message.answer("Максимум 10 фотографий.")
        return
    file_id = message.photo[-1].file_id
    photos.append(file_id)
    await state.update_data(photos=photos)
    await message.answer(f"Фото {len(photos)}/10 принято. Отправьте ещё или /done")


@router.message(AdminAddProduct.photos, Command("done"))
async def adm_product_photos_done(message: Message, state: FSMContext):
    await state.set_state(AdminAddProduct.sizes)
    await message.answer(
        "Введите <b>размеры</b> через запятую (например: XS, S, M, L, XL):"
    )


@router.message(AdminAddProduct.sizes)
async def adm_product_sizes(message: Message, state: FSMContext):
    sizes = [s.strip() for s in message.text.split(",") if s.strip()]
    await state.update_data(sizes=sizes)
    await state.set_state(AdminAddProduct.colors)
    await message.answer("Введите <b>цвета</b> через запятую (например: Чёрный, Белый, Серый):")


@router.message(AdminAddProduct.colors)
async def adm_product_colors(message: Message, state: FSMContext):
    colors = [c.strip() for c in message.text.split(",") if c.strip()]
    await state.update_data(colors=colors)
    await state.set_state(AdminAddProduct.stock)
    data = await state.get_data()
    sizes = data["sizes"]
    colors_list = colors
    await message.answer(
        f"Введите остатки для каждой комбинации размер+цвет.\n"
        f"Формат: размер,цвет,количество (по одному на строку)\n\n"
        f"Пример:\n" +
        "\n".join(f"{s},{c},10" for s in sizes for c in colors_list) +
        "\n\nОтправьте всё одним сообщением:"
    )
    await state.update_data(colors=colors)


@router.message(AdminAddProduct.stock)
async def adm_product_stock(message: Message, state: FSMContext):
    data = await state.get_data()
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
        await message.answer(f"Ошибки в строках:\n" + "\n".join(errors) + "\nПопробуйте ещё раз:")
        return

    product_id = db_add_product(
        name=data["name"],
        description=data["description"],
        price=data["price"],
        old_price=data.get("old_price"),
        photos=data.get("photos", []),
        sizes=data["sizes"],
        colors=data["colors"]
    )

    for size, color, qty in stock_data:
        db_set_stock(product_id, size, color, qty)

    await state.clear()
    await message.answer(
        f"✅ Товар <b>{data['name']}</b> добавлен (ID: {product_id})!",
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
    await state.set_state(AdminEditProduct.entering_value)

    prompts = {
        "name": "Введите новое название:",
        "description": "Введите новое описание:",
        "price": "Введите новую цену:",
        "old_price": "Введите новую старую цену (0 для удаления):",
        "sizes": "Введите размеры через запятую:",
        "colors": "Введите цвета через запятую:",
        "photos": "Отправьте новые фото (до 10), затем /done для завершения:",
    }

    if field == "photos":
        await state.update_data(photos=[])
        await state.set_state(AdminAddProduct.photos)
        await call.message.answer(prompts[field], reply_markup=ReplyKeyboardRemove())
    else:
        await call.message.answer(prompts.get(field, "Введите новое значение:"), reply_markup=ReplyKeyboardRemove())
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
            await message.answer("Неверный формат. Введите число:")
            return
    elif field == "old_price":
        try:
            v = float(message.text.strip().replace(",", "."))
            value = v if v > 0 else None
        except ValueError:
            await message.answer("Неверный формат:")
            return
    elif field in ("sizes", "colors"):
        value = [s.strip() for s in message.text.split(",") if s.strip()]
    else:
        value = message.text.strip()

    db_update_product_field(product_id, field, value)
    await state.clear()
    await message.answer(f"✅ Поле <b>{field}</b> обновлено.", reply_markup=kb_admin_main())


# ─────── ADMIN: STOCK ───────

@router.callback_query(F.data.startswith("adm_stock:"))
async def cb_adm_stock(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    product_id = int(call.data.split(":")[1])
    stock_rows = db_get_all_stock(product_id)
    product = db_get_product(product_id)

    if not stock_rows:
        text = f"📦 Остатки для <b>{product['name']}</b>: нет данных."
    else:
        lines = [f"📦 Остатки для <b>{product['name']}</b>:\n"]
        for row in stock_rows:
            lines.append(f"• {row['size']} / {row['color']}: {row['stock']} шт.")
        text = "\n".join(lines)

    await state.set_state(AdminEditProduct.entering_stock)
    await state.update_data(product_id=product_id)
    await call.message.answer(
        text + "\n\nВведите новые остатки (формат: размер,цвет,количество — по одному на строку):"
    )
    await call.answer()


@router.message(AdminEditProduct.entering_stock)
async def adm_stock_input(message: Message, state: FSMContext):
    data = await state.get_data()
    product_id = data["product_id"]
    errors = []
    for line in message.text.strip().splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) == 3:
            size, color, qty_str = parts
            try:
                qty = int(qty_str)
                db_set_stock(product_id, size, color, qty)
            except ValueError:
                errors.append(line)
        else:
            errors.append(line)

    if errors:
        await message.answer("Ошибки:\n" + "\n".join(errors))
    else:
        await message.answer("✅ Остатки обновлены.", reply_markup=kb_admin_main())
    await state.clear()


# ─────── ADMIN: ORDERS ───────

@router.message(F.text == "📦 Заказы", F.func(lambda m: is_admin(m.from_user.id)))
async def admin_orders(message: Message, state: FSMContext):
    await state.clear()
    orders = db_get_all_orders()
    if not orders:
        await message.answer("📦 Заказов пока нет.")
        return
    await message.answer("📦 <b>Все заказы:</b>", reply_markup=kb_admin_orders(orders))


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
    promo_info = f"\n🎟 Промокод: {order['promo_code']} (-{order['discount_amount']}₽)" if order["promo_code"] else ""

    status_emoji = {
        "pending": "⏳", "paid": "💳", "confirmed": "✅", "rejected": "❌"
    }.get(order["status"], "❓")

    user = db_get_user(order["tg_id"])
    username = f"@{user['username']}" if user and user["username"] else "—"

    text = (
        f"<b>Заказ #{order_id}</b> {status_emoji}\n\n"
        f"👤 {order['name']}\n"
        f"🧑 {username}\n"
        f"🆔 {order['tg_id']}\n"
        f"📱 {order['phone']}\n"
        f"📍 {order['address']}\n\n"
        f"🛍 {items_text}"
        f"{promo_info}\n\n"
        f"💰 Итого: {order['total']:.2f}₽\n"
        f"📅 {order['created_at'][:16]}"
    )

    kb = None
    if order["status"] == "paid":
        kb = kb_admin_order(order_id)

    await call.message.answer(text, reply_markup=kb)
    await call.answer()


# ─────── ADMIN: PROMOS ───────

@router.message(F.text == "🎟 Промокоды", F.func(lambda m: is_admin(m.from_user.id)))
async def admin_promos(message: Message, state: FSMContext):
    await state.clear()
    promos = db_get_all_promos()
    await message.answer("🎟 <b>Промокоды</b>", reply_markup=kb_admin_promos(promos))


@router.callback_query(F.data == "adm_back_promos")
async def cb_adm_back_promos(call: CallbackQuery):
    if not is_admin(call.from_user.id):
        return
    promos = db_get_all_promos()
    await call.message.edit_text("🎟 <b>Промокоды</b>", reply_markup=kb_admin_promos(promos))
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
    disc = f"{promo['value']}%" if promo["type"] == "percent" else f"{promo['value']}₽"
    status = "✅ Активен" if promo["is_active"] else "❌ Отключён"
    text = (
        f"🎟 <b>{promo['code']}</b>\n"
        f"Тип: {'Процент' if promo['type'] == 'percent' else 'Фиксированная'}\n"
        f"Скидка: {disc}\n"
        f"Статус: {status}"
    )
    await call.message.edit_text(text, reply_markup=kb_admin_promo_actions(promo_id, promo["is_active"]))
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
    await call.message.answer("Введите <b>код</b> промокода:", reply_markup=ReplyKeyboardRemove())
    await call.answer()


@router.message(AdminAddPromo.code)
async def adm_promo_code(message: Message, state: FSMContext):
    await state.update_data(code=message.text.strip().upper())
    await state.set_state(AdminAddPromo.ptype)
    await message.answer(
        "Выберите тип скидки:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="% Процент", callback_data="promo_type:percent"),
                InlineKeyboardButton(text="₽ Фиксированная", callback_data="promo_type:fixed"),
            ]
        ])
    )


@router.callback_query(AdminAddPromo.ptype, F.data.startswith("promo_type:"))
async def adm_promo_type(call: CallbackQuery, state: FSMContext):
    ptype = call.data.split(":")[1]
    await state.update_data(ptype=ptype)
    await state.set_state(AdminAddPromo.value)
    label = "процент (например: 15)" if ptype == "percent" else "сумму скидки (например: 10)"
    await call.message.answer(f"Введите {label}:")
    await call.answer()


@router.message(AdminAddPromo.value)
async def adm_promo_value(message: Message, state: FSMContext):
    try:
        value = float(message.text.strip().replace(",", "."))
    except ValueError:
        await message.answer("Неверный формат:")
        return
    data = await state.get_data()
    db_add_promo(data["code"], data["ptype"], value)
    await state.clear()
    disc = f"{value}%" if data["ptype"] == "percent" else f"{value}₽"
    await message.answer(
        f"✅ Промокод <b>{data['code']}</b> (-{disc}) создан.",
        reply_markup=kb_admin_main()
    )


# ─────── ADMIN: CLIENTS ───────

@router.message(F.text == "👥 Клиенты", F.func(lambda m: is_admin(m.from_user.id)))
async def admin_clients(message: Message, state: FSMContext):
    await state.clear()
    users = db_get_all_users()
    if not users:
        await message.answer("👥 Пользователей пока нет.")
        return
    lines = [f"👥 <b>Клиенты ({len(users)}):</b>\n"]
    for u in users:
        uname = f"@{u['username']}" if u["username"] else "—"
        lines.append(f"• {u['first_name']} {u['last_name'] or ''} | {uname} | ID: {u['tg_id']}")
    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000] + "\n..."
    await message.answer(text)


# ─────── ADMIN: BROADCAST ───────

@router.message(F.text == "📢 Рассылка", F.func(lambda m: is_admin(m.from_user.id)))
async def admin_broadcast_start(message: Message, state: FSMContext):
    await state.set_state(AdminBroadcast.message)
    await message.answer(
        "📢 Отправьте сообщение для рассылки (текст, фото или видео с подписью):",
        reply_markup=ReplyKeyboardRemove()
    )


@router.message(AdminBroadcast.message)
async def admin_broadcast_send(message: Message, state: FSMContext):
    await state.clear()
    users = db_get_all_users()
    sent = 0
    failed = 0

    for user in users:
        try:
            if message.photo:
                await bot.send_photo(
                    chat_id=user["tg_id"],
                    photo=message.photo[-1].file_id,
                    caption=message.caption or ""
                )
            elif message.video:
                await bot.send_video(
                    chat_id=user["tg_id"],
                    video=message.video.file_id,
                    caption=message.caption or ""
                )
            else:
                await bot.send_message(
                    chat_id=user["tg_id"],
                    text=message.text or message.caption or ""
                )
            sent += 1
            await asyncio.sleep(0.05)
        except Exception:
            failed += 1

    await message.answer(
        f"📢 Рассылка завершена.\n✅ Отправлено: {sent}\n❌ Ошибок: {failed}",
        reply_markup=kb_admin_main()
    )


# ─────── ADMIN: STATISTICS ───────

@router.message(F.text == "📊 Статистика", F.func(lambda m: is_admin(m.from_user.id)))
async def admin_stats(message: Message, state: FSMContext):
    await state.clear()
    users_count, orders_count, revenue, popular = db_stats()
    pop_text = ""
    if popular:
        pop_text = "\n\n🔥 <b>Популярные товары:</b>\n"
        for p in popular:
            pop_text += f"• {p['name']}\n"

    await message.answer(
        f"📊 <b>Статистика {SHOP_NAME}</b>\n\n"
        f"👥 Пользователей: {users_count}\n"
        f"📦 Заказов: {orders_count}\n"
        f"💰 Выручка: {revenue:.2f}₽"
        f"{pop_text}"
    )


# ─────── ADMIN: SETTINGS ───────

@router.message(F.text == "⚙️ Настройки", F.func(lambda m: is_admin(m.from_user.id)))
async def admin_settings(message: Message, state: FSMContext):
    await state.clear()
    payment_link = db_get_setting("payment_link")
    await message.answer(
        f"⚙️ <b>Настройки</b>\n\n"
        f"💳 Ссылка оплаты: {payment_link}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Изменить ссылку оплаты", callback_data="adm_set_paylink")]
        ])
    )


@router.callback_query(F.data == "adm_set_paylink")
async def cb_adm_set_paylink(call: CallbackQuery, state: FSMContext):
    if not is_admin(call.from_user.id):
        return
    await state.set_state(AdminSetPayLink.link)
    await call.message.answer("Введите новую ссылку для оплаты:", reply_markup=ReplyKeyboardRemove())
    await call.answer()


@router.message(AdminSetPayLink.link)
async def adm_set_paylink(message: Message, state: FSMContext):
    link = message.text.strip()
    db_set_setting("payment_link", link)
    await state.clear()
    await message.answer(f"✅ Ссылка оплаты обновлена:\n{link}", reply_markup=kb_admin_main())


# ─────── NOOP ───────

@router.callback_query(F.data == "noop")
async def cb_noop(call: CallbackQuery):
    await call.answer()


# ─────────────────────────────────────────────
# ADMIN FILTER HELPERS (lambda workaround)
# ─────────────────────────────────────────────

def make_admin_filter():
    async def _filter(message: Message):
        return is_admin(message.from_user.id)
    return _filter


# Re-register admin text handlers with proper filter
for _text, _handler in [
    ("🏠 Выход", admin_exit),
    ("🛍 Товары", admin_products),
    ("📦 Заказы", admin_orders),
    ("🎟 Промокоды", admin_promos),
    ("👥 Клиенты", admin_clients),
    ("📢 Рассылка", admin_broadcast_start),
    ("📊 Статистика", admin_stats),
    ("⚙️ Настройки", admin_settings),
]:
    pass  # Already registered with F.func above


# ─────────────────────────────────────────────
# PHOTOS DONE FOR EDIT
# ─────────────────────────────────────────────

@router.message(AdminAddProduct.photos, Command("done"))
async def adm_product_photos_done_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    if "product_id" in data:
        # editing existing product
        product_id = data["product_id"]
        photos = data.get("photos", [])
        db_update_product_field(product_id, "photos", photos)
        await state.clear()
        await message.answer(f"✅ Фото обновлены ({len(photos)} шт.).", reply_markup=kb_admin_main())
    else:
        # creating new product
        await state.set_state(AdminAddProduct.sizes)
        await message.answer("Введите <b>размеры</b> через запятую:")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

async def main():
    init_db()
    logger.info(f"Starting {SHOP_NAME} bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
