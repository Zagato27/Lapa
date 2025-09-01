## PostgreSQL: схема и использование таблиц

Этот документ зафиксирует актуальные таблицы в БД PostgreSQL, их структуру (колонки, PK/FK), примерные размеры и то, какими сервисами они используются. Также отмечены служебные таблицы PostGIS.

Подключение (docker-compose): хост `localhost`, порт `5432`, БД `lapa`, пользователь `lapa_user`.

### Сводная карта таблиц → сервисов

- public.users — user-service
- public.walker_verifications — user-service
- public.pets — pet-service
- public.pet_photos — pet-service
- public.pet_medical — pet-service
- public.orders — order-service
- public.order_locations — order-service
- public.order_reviews — order-service
- public.wallets — payment-service
- public.payment_methods — payment-service
- public.payments — payment-service
- public.payouts — payment-service
- public.transactions — payment-service
- public.media_files — media-service
- public.media_variants — media-service
- public.media_metadata — media-service
- public.media_albums — media-service
- public.media_access — media-service
- public.media_tags — media-service
- public.spatial_ref_sys — PostGIS (служебная)

Примечание: в коде присутствуют модели для chat-service, location-service, analytics-service, notification-service и api-gateway (напр. `gateway_route_stats`), но соответствующих таблиц в текущей БД не обнаружено (вероятно, не применены миграции или используются иные схемы/БД).

---

### public.users
Описание: Пользователи платформы, профиль, геоданные и настройки уведомлений.
Используют сервисы: user-service
PK: (id)
FK: нет обнаруженных явных FK
Оценка: approx_rows: n/a, size: 90112 bytes

Колонки:

| column | type | nullable | default |
|---|---|---|---|
| id | varchar | NO |  |
| email | varchar | NO |  |
| phone | varchar | NO |  |
| password_hash | varchar | NO |  |
| first_name | varchar | NO |  |
| last_name | varchar | NO |  |
| role | varchar | NO |  |
| avatar_url | varchar | YES |  |
| bio | text | YES |  |
| location | geometry | YES |  |
| latitude | float8 | YES |  |
| longitude | float8 | YES |  |
| is_active | bool | YES |  |
| is_verified | bool | YES |  |
| is_walker_verified | bool | YES |  |
| email_verified_at | timestamp | YES |  |
| phone_verified_at | timestamp | YES |  |
| rating | float8 | YES |  |
| total_orders | int4 | YES |  |
| completed_orders | int4 | YES |  |
| notifications_enabled | bool | YES |  |
| push_notifications | bool | YES |  |
| email_notifications | bool | YES |  |
| sms_notifications | bool | YES |  |
| experience_years | int4 | YES |  |
| services_offered | json | YES |  |
| work_schedule | json | YES |  |
| hourly_rate | float8 | YES |  |
| created_at | timestamp | YES |  |
| updated_at | timestamp | YES |  |
| last_login_at | timestamp | YES |  |

---

### public.walker_verifications
Описание: Верификации догвокеров: паспортные данные, опыт, статус проверки.
Используют сервисы: user-service
PK: (id)
FK: user_id → users(id)
Оценка: approx_rows: n/a, size: 32768 bytes

Колонки:

| column | type | nullable |
|---|---|---|
| id | varchar | NO |
| user_id | varchar | NO |
| passport_number | varchar | NO |
| passport_series | varchar | NO |
| passport_issued_by | text | NO |
| passport_issued_date | timestamp | NO |
| passport_expiry_date | timestamp | NO |
| experience_years | int4 | NO |
| services_offered | json | NO |
| work_schedule | json | NO |
| status | varchar | YES |
| admin_notes | text | YES |
| verified_by | varchar | YES |
| verified_at | timestamp | YES |
| passport_photo_front_url | varchar | YES |
| passport_photo_back_url | varchar | YES |
| additional_documents_urls | json | YES |
| created_at | timestamp | YES |
| updated_at | timestamp | YES |

---

### public.pets
Описание: Карточки питомцев пользователей: характеристики, здоровье, предпочтения.
Используют сервисы: pet-service
PK: (id)
FK: нет обнаруженных явных FK
Оценка: approx_rows: n/a, size: 32768 bytes

Колонки:

| column | type | nullable |
|---|---|---|
| id | varchar | NO |
| user_id | varchar | NO |
| name | varchar | NO |
| breed | varchar | NO |
| date_of_birth | timestamp | YES |
| age_years | int4 | YES |
| age_months | int4 | YES |
| gender | varchar | NO |
| color | varchar | YES |
| weight_kg | float8 | YES |
| size | varchar | YES |
| energy_level | varchar | YES |
| friendliness | varchar | YES |
| is_vaccinated | bool | YES |
| is_neutered | bool | YES |
| has_allergies | bool | YES |
| allergies_description | text | YES |
| special_needs | text | YES |
| medications | json | YES |
| medical_conditions | json | YES |
| is_friendly_with_dogs | bool | YES |
| is_friendly_with_cats | bool | YES |
| is_friendly_with_children | bool | YES |
| behavioral_notes | text | YES |
| walking_frequency | varchar | YES |
| walking_duration_minutes | int4 | YES |
| feeding_schedule | json | YES |
| favorite_activities | json | YES |
| walking_notes | text | YES |
| emergency_contact_name | varchar | YES |
| emergency_contact_phone | varchar | YES |
| veterinarian_name | varchar | YES |
| veterinarian_phone | varchar | YES |
| veterinarian_address | text | YES |
| avatar_url | varchar | YES |
| photos_count | int4 | YES |
| is_active | bool | YES |
| created_at | timestamp | YES |
| updated_at | timestamp | YES |

---

### public.pet_photos
Описание: Фотографии питомцев и их атрибуты/ссылки.
Используют сервисы: pet-service
PK: (id)
FK: pet_id → pets(id)
Оценка: approx_rows: n/a, size: 32768 bytes

Колонки (сокр.): id, pet_id, filename, original_filename, file_path, file_url, file_size, mime_type, width, height, thumbnail_path, thumbnail_url, photo_type, description, tags, is_active, uploaded_by, created_at, updated_at

---

### public.pet_medical
Описание: Медицинские записи питомцев (прививки, визиты, препараты).
Используют сервисы: pet-service
PK: (id)
FK: pet_id → pets(id)
Оценка: approx_rows: n/a, size: 32768 bytes

Колонки (сокр.): id, pet_id, record_type, title, description, medication_name/dosage/frequency, clinic/veterinarian*, event_date, next_visit_date, vaccination_due_date, cost, results, recommendations, documents_urls, is_completed, requires_follow_up, created_by, created_at, updated_at

---

### public.orders
Описание: Заказы на услуги (выгул, сидение и т.п.), статусы, расписание, сумма, гео.
Используют сервисы: order-service
PK: (id)
FK: нет обнаруженных явных FK
Оценка: approx_rows: n/a, size: 65536 bytes

Колонки (сокр.): id, client_id, walker_id, pet_id, order_type (enum), status (enum), scheduled_at, duration_minutes, actual_start_time, actual_end_time, location (geometry), latitude, longitude, address, walker_hourly_rate, total_amount, platform_commission, walker_earnings, special_instructions, walker_notes, client_rating, walker_rating, client_review, walker_review, created_at/updated_at/confirmed_at/completed_at/cancelled_at, cancellation_reason, cancelled_by, client_notified, walker_notified, review_reminder_sent

---

### public.order_locations
Описание: Точки/сэмплы геолокации в рамках заказа (трек движения).
Используют сервисы: order-service
PK: (id)
FK: order_id → orders(id)
Оценка: approx_rows: n/a, size: 49152 bytes

Колонки (сокр.): id, order_id, location (geometry), latitude, longitude, accuracy, address, city, district, location_type, timestamp, speed, altitude, heading, created_at

---

### public.order_reviews
Описание: Отзывы и оценки по заказам, модерация.
Используют сервисы: order-service
PK: (id)
FK: order_id → orders(id)
Оценка: approx_rows: n/a, size: 49152 bytes

Колонки (сокр.): id, order_id, reviewer_id/type, reviewee_id/type, rating, title, comment, punctuality_rating, communication_rating, pet_care_rating, overall_experience, is_public, is_anonymous, is_moderated, moderated_by/at, moderation_notes, created_at, updated_at

---

### public.wallets
Описание: Кошельки пользователей и агрегированные суммы.
Используют сервисы: payment-service
PK: (id)
FK: нет обнаруженных явных FK
Оценка: approx_rows: n/a, size: 32768 bytes

Колонки (сокр.): id, user_id, balance, currency, min/max_balance, daily/monthly_limit, is_active, is_frozen, frozen_reason, totals*, bonus_balance, referral_balance, auto_topup_enabled/amount/threshold, pin_code_hash, two_factor_enabled, created_at, updated_at, last_operation_at

---

### public.payment_methods
Описание: Способы оплаты пользователей (тип/провайдер, маски, зашифр.данные).
Используют сервисы: payment-service
PK: (id)
FK: нет обнаруженных явных FK
Оценка: approx_rows: n/a, size: 32768 bytes

Колонки (сокр.): id, user_id, type (enum), provider, name/title, encrypted_data, provider_data, masked_number, masked_email, is_active, is_default, is_verified, daily_limit, monthly_limit, totals*, last_used_at, verification_attempts, last_verification_at, fraud_score, created_at, updated_at, expires_at

---

### public.payments
Описание: Платежи (входящие), статусы и суммы.
Используют сервисы: payment-service
PK: (id)
FK: payment_method_id → payment_methods(id)
Оценка: approx_rows: n/a, size: 40960 bytes

Колонки (сокр.): id, order_id, user_id, payment_type (enum), status (enum), provider (enum), amount, currency, platform_commission, provider_commission, net_amount, provider_payment_id, provider_data, payment_method_id, description, extra_metadata, created_at, updated_at, paid_at, cancelled_at, refunded_at, refund_amount, refund_reason, is_test, ip_address, user_agent, webhook_received, notification_sent

---

### public.payouts
Описание: Выплаты исполнителям/партнерам; периоды и реквизиты.
Используют сервисы: payment-service
PK: (id)
FK: нет обнаруженных явных FK
Оценка: approx_rows: n/a, size: 32768 bytes

Колонки (сокр.): id, user_id, amount, currency, platform_fee, net_amount, status (enum), method (enum), period_start, period_end, recipient_name, recipient_data, order_ids, provider_payout_id, provider_data, processed_by/at, failure_reason, is_test, priority, created_at, updated_at, scheduled_at

---

### public.transactions
Описание: Проводки по счетам: платежи, выплаты, пополнения, комиссии.
Используют сервисы: payment-service
PK: (id)
FK: payment_id → payments(id); payout_id → payouts(id)
Оценка: approx_rows: n/a, size: 32768 bytes

Колонки (сокр.): id, payment_id, payout_id, order_id, user_id, recipient_id, transaction_type (enum), status (enum), amount, currency, fee, net_amount, balance_before, balance_after, description, extra_metadata, created_at, updated_at, processed_at, is_test, ip_address, user_agent, session_id, created_by, approved_by, failure_reason

---

### public.media_files
Описание: Базовая сущность медиафайла, место хранения, размеры и счетчики.
Используют сервисы: media-service
PK: (id)
FK: album_id → media_albums(id)
Оценка: approx_rows: n/a, size: 81920 bytes

Колонки (сокр.): id, filename, file_path/url/public_url, media_type (enum), status (enum), storage_backend (enum), owner_id, is_public, album_id, file_size, mime_type, width/height, duration, bitrate, processed_at, processing_errors, thumbnail_*, optimized_*, file_hash, is_encrypted, encryption_key, title, description, tags, colors, location, camera_info, view_count, download_count, like_count, share_count, created_at, updated_at, expires_at, last_accessed_at

---

### public.media_variants
Описание: Различные варианты одного медиафайла (превью/резайзы/конвертации).
Используют сервисы: media-service
PK: (id)
FK: media_file_id → media_files(id)
Оценка: approx_rows: n/a, size: 32768 bytes

Колонки (сокр.): id, media_file_id, variant_type (enum), status (enum), name, description, file_path/url, file_size, mime_type, file_hash, width/height, quality, format, compression_level, bitrate, frame_rate, duration, processing_params, processing_time, processing_errors, view_count, download_count, last_accessed_at, metadata, created_at, updated_at, completed_at

---

### public.media_metadata
Описание: Технические метаданные (EXIF/кодеки/цветовые профили/гео и пр.).
Используют сервисы: media-service
PK: (id)
FK: media_file_id → media_files(id)
Оценка: approx_rows: n/a, size: 32768 bytes

Колонки (сокр.): id, media_file_id, camera_make/model, lens_make/model, focal_length, aperture, shutter_speed, iso, flash, exposure_program, latitude/longitude/altitude, location_*, date_taken/digitized/original, color_space/profile, dominant_colors, color_histogram, image_* (width/height/resolution/orientation/compression), video_* (codec/bitrate/frame_rate/aspect_ratio), audio_* (codec/channels/sample_rate), software, device_name/model, os_version, keywords/categories/tags, copyright/artist/creator, rating, quality_score, raw_metadata, custom_metadata, created_at, updated_at, extracted_at

---

### public.media_albums
Описание: Альбомы медиафайлов (владельцы, доступ, лимиты, счетчики).
Используют сервисы: media-service
PK: (id)
FK: cover_file_id → media_files(id)
Оценка: approx_rows: n/a, size: 49152 bytes

Колонки (сокр.): id, name, description, album_type (enum), status (enum), owner_id, pet_id, order_id, is_public, is_shared, allow_upload, allow_download, max_files, max_file_size_mb, allowed_types, cover_file_id, total_files, total_size, image_count, video_count, audio_count, tags, settings, created_at, updated_at, last_activity_at

---

### public.media_access
Описание: Правила и токены доступа к медиафайлам (уровни/типы/лимиты).
Используют сервисы: media-service
PK: (id)
FK: нет обнаруженных явных FK
Оценка: approx_rows: n/a, size: 57344 bytes

Колонки (сокр.): id, media_file_id, access_type (enum), access_level (enum), status (enum), user_id, group_id, token, max_views, max_downloads, expires_at, password_hash, view_count, download_count, last_access_at, granted_by, granted_at, description, metadata, created_at, updated_at

---

### public.media_tags
Описание: Теги для классификации медиа.
Используют сервисы: media-service
PK: (id)
FK: нет обнаруженных явных FK
Оценка: approx_rows: n/a, size: 49152 bytes

Колонки (сокр.): id, name, slug, tag_type (enum), status (enum), description, color, creator_id, is_public, is_featured, usage_count, media_count, icon_url, icon_emoji, metadata, created_at, updated_at, last_used_at

---

### public.spatial_ref_sys (PostGIS)
Описание: Справочник систем координат (SRID) — служебная таблица PostGIS.
Используют сервисы: все гео-функции (косвенно через PostGIS)
PK: (srid)
Оценка: approx_rows: ~8500, size: 7315456 bytes

Колонки: srid, auth_name, auth_srid, srtext, proj4text

---

### Внешние ключи (итогом по public)

- media_albums.cover_file_id → media_files.id
- media_files.album_id → media_albums.id
- media_metadata.media_file_id → media_files.id
- media_variants.media_file_id → media_files.id
- order_locations.order_id → orders.id
- order_reviews.order_id → orders.id
- payments.payment_method_id → payment_methods.id
- pet_medical.pet_id → pets.id
- pet_photos.pet_id → pets.id
- transactions.payment_id → payments.id
- transactions.payout_id → payouts.id
- walker_verifications.user_id → users.id

---

### ENUM-типы (public)

- accesslevel: NONE, READ, WRITE, ADMIN
- accessstatus: ACTIVE, EXPIRED, REVOKED, PENDING
- accesstype: VIEW, DOWNLOAD, EDIT, DELETE, SHARE
- albumstatus: ACTIVE, ARCHIVED, DELETED, PRIVATE
- albumtype: USER, PET, ORDER, SYSTEM, SHARED
- mediastatus: UPLOADING, UPLOADED, PROCESSING, READY, FAILED, DELETED
- mediatype: IMAGE, VIDEO, AUDIO, DOCUMENT, ARCHIVE
- orderstatus: PENDING, CONFIRMED, IN_PROGRESS, COMPLETED, CANCELLED, NO_WALKER
- ordertype: SINGLE_WALK, REGULAR_WALK, PET_SITTING, PET_BOARDING
- paymentmethodtype: BANK_CARD, ELECTRONIC_WALLET, BANK_ACCOUNT, SBP, CRYPTO
- paymentprovider: STRIPE, YOOKASSA, TINKOFF, SBP, WALLET, CASH
- paymentstatus: PENDING, PROCESSING, COMPLETED, FAILED, CANCELLED, REFUNDED, PARTIALLY_REFUNDED
- paymenttype: ORDER_PAYMENT, WALLET_TOPUP, SUBSCRIPTION, DONATION, FINE, BONUS
- payoutmethod: BANK_CARD, BANK_ACCOUNT, ELECTRONIC_WALLET, CASH, SBP
- payoutstatus: PENDING, PROCESSING, COMPLETED, FAILED, CANCELLED, ON_HOLD
- storagebackend: LOCAL, S3, CLOUDINARY, IMGUR
- tagstatus: ACTIVE, DEPRECATED, BANNED
- tagtype: USER, SYSTEM, AUTO, CATEGORY
- transactionstatus: PENDING, PROCESSING, COMPLETED, FAILED, CANCELLED
- transactiontype: PAYMENT, REFUND, PAYOUT, TRANSFER, DEPOSIT, WITHDRAWAL, FEE, BONUS, ADJUSTMENT
- variantstatus: CREATING, READY, FAILED, DELETED
- varianttype: ORIGINAL, THUMBNAIL, OPTIMIZED, RESIZED, COMPRESSED, CONVERTED, WATERMARKED

---

### Служебные схемы PostGIS

- Схема `tiger`: addr, addrfeat, bg, county, county_lookup, countysub_lookup, cousub, direction_lookup, edges, faces, featnames, geocode_settings, geocode_settings_default, loader_lookuptables, loader_platform, loader_variables, pagc_gaz, pagc_lex, pagc_rules, place, place_lookup, secondary_unit_lookup, state, state_lookup, street_type_lookup, tabblock, tabblock20, tract, zcta5, zip_lookup, zip_lookup_all, zip_lookup_base, zip_state, zip_state_loc
- Схема `topology`: layer, topology

Примечание: таблицы `geometry_columns`/`geography_columns` присутствуют как представления/служебные объекты PostGIS в `public`.


