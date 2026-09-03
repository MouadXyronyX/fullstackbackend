-- ========================================
-- Al-Quds Furniture - Database Schema
-- Run this in Supabase SQL Editor
-- ========================================


CREATE TABLE roles (
	id SERIAL NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
)

;
CREATE INDEX ix_roles_id ON roles (id);

CREATE TABLE categories (
	id SERIAL NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	description TEXT, 
	image_url VARCHAR(500), 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id)
)

;
CREATE INDEX ix_categories_id ON categories (id);

CREATE TABLE pages (
	id SERIAL NOT NULL, 
	slug VARCHAR(255) NOT NULL, 
	title VARCHAR(255) NOT NULL, 
	content TEXT, 
	is_published BOOLEAN, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id)
)

;
CREATE UNIQUE INDEX ix_pages_slug ON pages (slug);
CREATE INDEX ix_pages_id ON pages (id);

CREATE TABLE notifications (
	id SERIAL NOT NULL, 
	type VARCHAR(50) NOT NULL, 
	reference_id VARCHAR(50), 
	message TEXT NOT NULL, 
	is_read BOOLEAN, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id)
)

;
CREATE INDEX ix_notifications_id ON notifications (id);

CREATE TABLE settings (
	id SERIAL NOT NULL, 
	key VARCHAR(255) NOT NULL, 
	value TEXT, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (key)
)

;
CREATE INDEX ix_settings_id ON settings (id);

CREATE TABLE users (
	id SERIAL NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	email VARCHAR(255), 
	phone VARCHAR(50), 
	password_hash VARCHAR(255) NOT NULL, 
	role_id INTEGER NOT NULL, 
	is_active BOOLEAN, 
	totp_secret VARCHAR(255), 
	totp_enabled BOOLEAN, 
	failed_login_attempts INTEGER, 
	locked_until TIMESTAMP WITH TIME ZONE, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (email), 
	UNIQUE (phone), 
	FOREIGN KEY(role_id) REFERENCES roles (id)
)

;
CREATE INDEX ix_users_id ON users (id);

CREATE TABLE products (
	id SERIAL NOT NULL, 
	name VARCHAR(255) NOT NULL, 
	price FLOAT NOT NULL, 
	description TEXT, 
	category_id INTEGER, 
	is_available BOOLEAN, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(category_id) REFERENCES categories (id)
)

;
CREATE INDEX ix_products_id ON products (id);

CREATE TABLE product_images (
	id SERIAL NOT NULL, 
	product_id INTEGER NOT NULL, 
	image_url VARCHAR(500) NOT NULL, 
	"order" INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(product_id) REFERENCES products (id)
)

;
CREATE INDEX ix_product_images_id ON product_images (id);

CREATE TABLE orders (
	id SERIAL NOT NULL, 
	order_code VARCHAR(50) NOT NULL, 
	user_id INTEGER, 
	guest_name VARCHAR(255), 
	guest_phone VARCHAR(50), 
	guest_email VARCHAR(255), 
	wilaya VARCHAR(100) NOT NULL, 
	commune VARCHAR(100) NOT NULL, 
	address TEXT NOT NULL, 
	note TEXT, 
	status VARCHAR(50), 
	total_price FLOAT NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;
CREATE UNIQUE INDEX ix_orders_order_code ON orders (order_code);
CREATE INDEX ix_orders_id ON orders (id);

CREATE TABLE chats (
	id SERIAL NOT NULL, 
	user_id INTEGER, 
	guest_identifier VARCHAR(255), 
	product_id INTEGER, 
	is_active BOOLEAN, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	updated_at TIMESTAMP WITH TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(product_id) REFERENCES products (id)
)

;
CREATE INDEX ix_chats_id ON chats (id);

CREATE TABLE sessions (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	refresh_token VARCHAR(500) NOT NULL, 
	expires_at TIMESTAMP WITH TIME ZONE NOT NULL, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
)

;
CREATE INDEX ix_sessions_id ON sessions (id);

CREATE TABLE order_items (
	id SERIAL NOT NULL, 
	order_id INTEGER NOT NULL, 
	product_id INTEGER NOT NULL, 
	quantity INTEGER NOT NULL, 
	price_at_order FLOAT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(order_id) REFERENCES orders (id), 
	FOREIGN KEY(product_id) REFERENCES products (id)
)

;
CREATE INDEX ix_order_items_id ON order_items (id);

CREATE TABLE messages (
	id SERIAL NOT NULL, 
	chat_id INTEGER NOT NULL, 
	sender_type VARCHAR(50) NOT NULL, 
	content TEXT NOT NULL, 
	is_read BOOLEAN, 
	created_at TIMESTAMP WITH TIME ZONE DEFAULT now(), 
	PRIMARY KEY (id), 
	FOREIGN KEY(chat_id) REFERENCES chats (id)
)

;
CREATE INDEX ix_messages_id ON messages (id);

-- ========================================
-- Seed Data
-- ========================================

-- Roles
INSERT INTO roles (id, name) VALUES (1, 'admin') ON CONFLICT (id) DO NOTHING;
INSERT INTO roles (id, name) VALUES (2, 'customer') ON CONFLICT (id) DO NOTHING;

-- Admin user (email: admin@alquds-store.com / password: admin123456)
INSERT INTO users (name, email, phone, password_hash, role_id, is_active)
VALUES ('مدير المتجر', 'admin@alquds-store.com', '0555000000', '$2b$12$yueHjUP8w0PEtdUJjcfNcuiKmetz9uMmnepm9otuCDkAssxQIDN7W', 1, true);

-- Categories
INSERT INTO categories (id, name, description, image_url) VALUES (1, 'غرف المعيشة', 'أثاث غرف المعيشة الفاخر', 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800') ON CONFLICT (id) DO NOTHING;
INSERT INTO categories (id, name, description, image_url) VALUES (2, 'غرف النوم', 'غرف نوم عصرية وكلاسيكية', 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800') ON CONFLICT (id) DO NOTHING;
INSERT INTO categories (id, name, description, image_url) VALUES (3, 'الكراسي والطاولات', 'كراسي وطاولات طعام ومكتب', 'https://images.unsplash.com/photo-1506439773649-6e0eb8cfb237?w=800') ON CONFLICT (id) DO NOTHING;

-- Products
INSERT INTO products (id, name, price, description, category_id, is_available) VALUES (1, 'أريكة كلاسيكية فاخرة', 85000, 'أريكة كلاسيكية فاخرة مصنوعة من أجود أنواع القماش المخملي مع تفاصيل ذهبية.', 1, true) ON CONFLICT (id) DO NOTHING;
INSERT INTO products (id, name, price, description, category_id, is_available) VALUES (2, 'طقم كنب عصري 3 قطع', 120000, 'طقم كنب عصري مكون من 3 قطع بتصميم أنيق وناعم.', 1, true) ON CONFLICT (id) DO NOTHING;
INSERT INTO products (id, name, price, description, category_id, is_available) VALUES (3, 'طاولة طعام زجاجية 6 كراسي', 95000, 'طاولة طعام عصرية من الزجاج المقسّى مع قاعدة خشبية متينة.', 3, true) ON CONFLICT (id) DO NOTHING;
INSERT INTO products (id, name, price, description, category_id, is_available) VALUES (4, 'سرير ملكي مع خزانة', 135000, 'سرير ملكي فاخر مقاس 180×200 سم مع خزانة ملابس كبيرة مطابقة.', 2, true) ON CONFLICT (id) DO NOTHING;
INSERT INTO products (id, name, price, description, category_id, is_available) VALUES (5, 'كرسي مكتب مريح', 35000, 'كرسي مكتب مريح مع مسند للظهر ودعم للرقبة.', 3, true) ON CONFLICT (id) DO NOTHING;
INSERT INTO products (id, name, price, description, category_id, is_available) VALUES (6, 'طاولة جانبية ذهبية', 28000, 'طاولة جانبية صغيرة بتصميم فاخر. قاعدة ذهبية مع سطح رخامي.', 1, true) ON CONFLICT (id) DO NOTHING;
INSERT INTO products (id, name, price, description, category_id, is_available) VALUES (7, 'غرفة نوم كاملة 5 قطع', 220000, 'غرفة نوم كاملة مكونة من سرير + خزانة + تسريحة + مرآة + 2 كومودينو.', 2, true) ON CONFLICT (id) DO NOTHING;
INSERT INTO products (id, name, price, description, category_id, is_available) VALUES (8, 'أريكة استرخاء قابلة للطي', 55000, 'أريكة استرخاء مريحة قابلة للطي لتتحول إلى سرير.', 1, true) ON CONFLICT (id) DO NOTHING;
INSERT INTO products (id, name, price, description, category_id, is_available) VALUES (9, 'طقم كراسي طعام 4 قطع', 65000, 'طقم كراسي طعام أنيقة مكون من 4 كراسي. إطار خشبي متين.', 3, true) ON CONFLICT (id) DO NOTHING;
INSERT INTO products (id, name, price, description, category_id, is_available) VALUES (10, 'خزانة كتب وتزيين', 72000, 'خزانة كتب عصرية بتصميم مفتوح. أرفف متعددة للكتب والديكور.', 1, true) ON CONFLICT (id) DO NOTHING;
INSERT INTO products (id, name, price, description, category_id, is_available) VALUES (11, 'سرير أطفال مع مرتبة', 68000, 'سرير أطفال آمن ومريح مقاس 90×190 سم.', 2, true) ON CONFLICT (id) DO NOTHING;
INSERT INTO products (id, name, price, description, category_id, is_available) VALUES (12, 'طاولة مكتب خشبية', 42000, 'طاولة مكتب خشبية عملية مع أدراج للتخزين.', 3, true) ON CONFLICT (id) DO NOTHING;

-- Product Images
INSERT INTO product_images (product_id, image_url, "order") VALUES (1, 'https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800', 0) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (1, 'https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?w=800', 1) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (1, 'https://images.unsplash.com/photo-1540574163026-643ea20ade25?w=800', 2) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (2, 'https://images.unsplash.com/photo-1550258987-190a2d41a8ba?w=800', 0) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (2, 'https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?w=800', 1) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (3, 'https://images.unsplash.com/photo-1615066390977-6c602d0e0e10?w=800', 0) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (3, 'https://images.unsplash.com/photo-1617806118233-18e1de247200?w=800', 1) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (4, 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800', 0) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (4, 'https://images.unsplash.com/photo-1616594039964-ae9021a400a0?w=800', 1) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (5, 'https://images.unsplash.com/photo-1506439773649-6e0eb8cfb237?w=800', 0) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (5, 'https://images.unsplash.com/photo-1592078615290-033ee584e267?w=800', 1) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (6, 'https://images.unsplash.com/photo-1533090481720-856c6e3c1fdc?w=800', 0) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (6, 'https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=800', 1) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (7, 'https://images.unsplash.com/photo-1616594039964-ae9021a400a0?w=800', 0) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (7, 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800', 1) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (8, 'https://images.unsplash.com/photo-1540574163026-643ea20ade25?w=800', 0) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (9, 'https://images.unsplash.com/photo-1503602642458-232111445657?w=800', 0) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (9, 'https://images.unsplash.com/photo-1506439773649-6e0eb8cfb237?w=800', 1) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (10, 'https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=800', 0) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (11, 'https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800', 0) ON CONFLICT DO NOTHING;
INSERT INTO product_images (product_id, image_url, "order") VALUES (12, 'https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=800', 0) ON CONFLICT DO NOTHING;

-- Pages
INSERT INTO pages (slug, title, content, is_published) VALUES ('about', 'من نحن', '<h2>مرحباً بكم في اثاث القدس</h2><p>نحن متخصصون في بيع الأثاث الفاخر بأفضل الأسعار.</p>', true) ON CONFLICT (slug) DO NOTHING;
INSERT INTO pages (slug, title, content, is_published) VALUES ('return-policy', 'سياسة الاستبدال والإرجاع', '<h2>سياسة الاستبدال والإرجاع</h2><p>يمكنك استبدال أو إرجاع المنتجات خلال 7 أيام من تاريخ الاستلام.</p>', true) ON CONFLICT (slug) DO NOTHING;
INSERT INTO pages (slug, title, content, is_published) VALUES ('how-to-order', 'كيفية الطلب', '<h2>كيفية الطلب</h2><ol><li>تصفح المنتجات واختر ما يعجبك</li><li>أضف المنتج إلى السلة</li><li>املأ بيانات التوصيل</li><li>استلم طلبك في أقرب وقت</li></ol>', true) ON CONFLICT (slug) DO NOTHING;

-- Settings
INSERT INTO settings (key, value) VALUES ('store_name', 'اثاث القدس') ON CONFLICT (key) DO NOTHING;
INSERT INTO settings (key, value) VALUES ('store_description', 'متجر الأثاث الفاخر في الجزائر') ON CONFLICT (key) DO NOTHING;
INSERT INTO settings (key, value) VALUES ('facebook_url', 'https://facebook.com/alqudsfurniture') ON CONFLICT (key) DO NOTHING;
INSERT INTO settings (key, value) VALUES ('instagram_url', 'https://instagram.com/alqudsfurniture') ON CONFLICT (key) DO NOTHING;
INSERT INTO settings (key, value) VALUES ('whatsapp_number', '213555000000') ON CONFLICT (key) DO NOTHING;
INSERT INTO settings (key, value) VALUES ('phone', '0555 00 00 00') ON CONFLICT (key) DO NOTHING;
INSERT INTO settings (key, value) VALUES ('email', 'contact@alquds-store.com') ON CONFLICT (key) DO NOTHING;
INSERT INTO settings (key, value) VALUES ('address', 'الجزائر العاصمة، الجزائر') ON CONFLICT (key) DO NOTHING;
INSERT INTO settings (key, value) VALUES ('working_hours', 'السبت - الخميس: 9:00 - 20:00') ON CONFLICT (key) DO NOTHING;

-- ========================================
-- Done! All tables and seed data created.
-- ========================================