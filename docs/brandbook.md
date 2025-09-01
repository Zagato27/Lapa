# Брендбук Lapa (Natural Premium)

## Палитра
- Forest `#1F5D50`
- Sage `#A3C9A8`
- Sand `#E8DCC9`
- Charcoal `#2B2F36`
- Copper `#C57B57`

Пропорции: 60% Sand, 25–30% Forest, 10–15% Sage, 5–8% Copper, 2–5% Charcoal.

## Контраст
WCAG 2.1 AA: текст ≥4.5:1 (обычный) и ≥3:1 (крупный). Проверяйте пары: Charcoal/Sand, Forest/Sand, Copper/Sand.

## Типографика
- Шрифт: Inter (next/font), line-height ~1.6
- Иерархия: H1/H2 — Forest; навигация — Forest/Charcoal; текст — Charcoal; CTA — Copper.

## Логотип
- Основной: Forest на Sand; инверсия: Sand/белый на Forest; моно: Charcoal/белый.
- Охранное поле: модуль «x» по периметру.
- Минимальный размер: фиксировать в макетах перед печатью.

## UI
- Primary CTA: Copper фон, белый текст, hover темнее, focus Forest.
- Secondary: контур Forest, hover лёгкий Sage.
- Карточки: Sand/Sage фон, заголовки Forest, текст Charcoal.

## Изображения и иконки
Естественный свет, природность; иконки — линейные/минимальные, цвет Charcoal/Forest, акценты Copper точечно.

## Тёмная тема
Автовыбор после заката по геолокации (fallback: Москва). Переопределение переменных:
```
[data-theme="dark"] {
  --color-forest: #1C4B41;
  --color-sage: #7FAF8A;
  --color-sand: #1A1C1F;
  --color-charcoal: #E8E9EC;
  --color-copper: #D0876A;
}
```

## Чек‑лист внедрения
- Утвердить палитру и 60–30–10
- Зафиксировать пары контраста и примеры
- Выбрать шрифтовую пару и иерархию
- Описать версии логотипа и поля
- Примеры макетов (веб/печать)


