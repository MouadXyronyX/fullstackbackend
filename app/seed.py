from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash
from app.models.user import User, Role
from app.models.category import Category
from app.models.product import Product, ProductImage
from app.models.page import Page
from app.models.setting import Setting


def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(Role).count() > 0:
            print("Database already seeded.")
            return

        # Roles
        admin_role = Role(name="admin")
        customer_role = Role(name="customer")
        db.add_all([admin_role, customer_role])
        db.flush()

        # Admin user
        admin = User(
            name="مدير المتجر",
            email="admin@alquds-store.com",
            phone="0555000000",
            password_hash=get_password_hash("admin123456"),
            role_id=admin_role.id,
        )
        db.add(admin)

        # Categories
        cat1 = Category(name="غرف المعيشة", description="أثاث غرف المعيشة الفاخر", image_url="https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800")
        cat2 = Category(name="غرف النوم", description="غرف نوم عصرية وكلاسيكية", image_url="https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800")
        cat3 = Category(name="الكراسي والطاولات", description="كراسي وطاولات طعام ومكتب", image_url="https://images.unsplash.com/photo-1506439773649-6e0eb8cfb237?w=800")
        db.add_all([cat1, cat2, cat3])
        db.flush()

        # Products
        products_data = [
            {
                "name": "أريكة كلاسيكية فاخرة",
                "price": 85000,
                "description": "أريكة كلاسيكية فاخرة مصنوعة من أجود أنواع القماش المخملي مع تفاصيل ذهبية. مثالية لغرف المعيشة الفخمة. تأتي مع وسائد مريحة ومساند ذهبية.",
                "category_id": cat1.id,
                "images": [
                    "https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=800",
                    "https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?w=800",
                    "https://images.unsplash.com/photo-1540574163026-643ea20ade25?w=800",
                ],
            },
            {
                "name": "طقم كنب عصري 3 قطع",
                "price": 120000,
                "description": "طقم كنب عصري مكون من 3 قطع بتصميم أنيق وناعم. أقمشة عالية الجودة مع ألوان محايدة تناسب أي ديكور.",
                "category_id": cat1.id,
                "images": [
                    "https://images.unsplash.com/photo-1550258987-190a2d41a8ba?w=800",
                    "https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?w=800",
                ],
            },
            {
                "name": "طاولة طعام زجاجية 6 كراسي",
                "price": 95000,
                "description": "طاولة طعام عصرية من الزجاج المقسّى مع قاعدة خشبية متينة. تأتي مع 6 كراسي مبطنة بالقماش الفاخر.",
                "category_id": cat3.id,
                "images": [
                    "https://images.unsplash.com/photo-1615066390977-6c602d0e0e10?w=800",
                    "https://images.unsplash.com/photo-1617806118233-18e1de247200?w=800",
                ],
            },
            {
                "name": "سرير ملكي مع خزانة",
                "price": 135000,
                "description": "سرير ملكي فاخر مقاس 180×200 سم مع خزانة ملابس كبيرة مطابقة. خشب طبيعي فاخر مع تشطيب ذهبي.",
                "category_id": cat2.id,
                "images": [
                    "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800",
                    "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?w=800",
                ],
            },
            {
                "name": "كرسي مكتب مريح",
                "price": 35000,
                "description": "كرسي مكتب مريح مع مسند للظهر ودعم للرقبة. قابل لتعديل الارتفاع مع عجلات ناعمة الحركة.",
                "category_id": cat3.id,
                "images": [
                    "https://images.unsplash.com/photo-1506439773649-6e0eb8cfb237?w=800",
                    "https://images.unsplash.com/photo-1592078615290-033ee584e267?w=800",
                ],
            },
            {
                "name": "طاولة جانبية ذهبية",
                "price": 28000,
                "description": "طاولة جانبية صغيرة بتصميم فاخر. قاعدة ذهبية مع سطح رخامي. مثالية بجانب الأريكة أو السرير.",
                "category_id": cat1.id,
                "images": [
                    "https://images.unsplash.com/photo-1533090481720-856c6e3c1fdc?w=800",
                    "https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=800",
                ],
            },
            {
                "name": "غرفة نوم كاملة 5 قطع",
                "price": 220000,
                "description": "غرفة نوم كاملة مكونة من سرير + خزانة + تسريحة + مرآة + 2 كومودينو. تصميم كلاسيكي فاخر بلون عاجي مع ذهبي.",
                "category_id": cat2.id,
                "images": [
                    "https://images.unsplash.com/photo-1616594039964-ae9021a400a0?w=800",
                    "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800",
                ],
            },
            {
                "name": "أريكة استرخاء قابلة للطي",
                "price": 55000,
                "description": "أريكة استرخاء مريحة قابلة للطي لتتحول إلى سرير. مثالية لغرفة الضيوف أو غرفة المعيشة.",
                "category_id": cat1.id,
                "images": [
                    "https://images.unsplash.com/photo-1540574163026-643ea20ade25?w=800",
                ],
            },
            {
                "name": "طقم كراسي طعام 4 قطع",
                "price": 65000,
                "description": "طقم كراسي طعام أنيقة مكون من 4 كراسي. إطار خشبي متين مع تنجيد قماشي فاخر.",
                "category_id": cat3.id,
                "images": [
                    "https://images.unsplash.com/photo-1503602642458-232111445657?w=800",
                    "https://images.unsplash.com/photo-1506439773649-6e0eb8cfb237?w=800",
                ],
            },
            {
                "name": "خزانة كتب وتزيين",
                "price": 72000,
                "description": "خزانة كتب عصرية بتصميم مفتوح. أرفف متعددة للكتب والديكور. خشب متين بلون جوزي غامق.",
                "category_id": cat1.id,
                "images": [
                    "https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=800",
                ],
            },
            {
                "name": "سرير أطفال مع مرتبة",
                "price": 68000,
                "description": "سرير أطفال آمن ومريح مقاس 90×190 سم. تصميم عصري مع حواف مستديرة. يشمل المرتبة.",
                "category_id": cat2.id,
                "images": [
                    "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?w=800",
                ],
            },
            {
                "name": "طاولة مكتب خشبية",
                "price": 42000,
                "description": "طاولة مكتب خشبية عملية مع أدراج للتخزين. سطح واسع يناسب الكمبيوتر واللوازم.",
                "category_id": cat3.id,
                "images": [
                    "https://images.unsplash.com/photo-1518455027359-f3f8164ba6bd?w=800",
                ],
            },
        ]

        for p_data in products_data:
            images = p_data.pop("images")
            product = Product(**p_data)
            db.add(product)
            db.flush()
            for idx, url in enumerate(images):
                db.add(ProductImage(product_id=product.id, image_url=url, order=idx))

        # Pages
        pages_data = [
            {"slug": "about", "title": "من نحن", "content": "<h2>مرحباً بكم في اثاث القدس</h2><p>نحن متخصصون في بيع الأثاث الفاخر بأفضل الأسعار. نوفر لكم تشكيلة واسعة من أجود أنواع الأثاث العصري والكلاسيكي.</p>"},
            {"slug": "return-policy", "title": "سياسة الاستبدال والإرجاع", "content": "<h2>سياسة الاستبدال والإرجاع</h2><p>يمكنك استبدال أو إرجاع المنتجات خلال 7 أيام من تاريخ الاستلام بشرط أن تكون بحالتها الأصلية.</p>"},
            {"slug": "how-to-order", "title": "كيفية الطلب", "content": "<h2>كيفية الطلب</h2><ol><li>تصفح المنتجات واختر ما يعجبك</li><li>أضف المنتج إلى السلة</li><li>املأ بيانات التوصيل</li><li>استلم طلبك في أقرب وقت</li></ol>"},
        ]
        for p_data in pages_data:
            db.add(Page(**p_data))

        # Default settings
        default_settings = {
            "store_name": "اثاث القدس",
            "store_description": "متجر الأثاث الفاخر في الجزائر",
            "facebook_url": "https://facebook.com/alqudsfurniture",
            "instagram_url": "https://instagram.com/alqudsfurniture",
            "whatsapp_number": "213555000000",
            "phone": "0555 00 00 00",
            "email": "contact@alquds-store.com",
            "address": "الجزائر العاصمة، الجزائر",
            "working_hours": "السبت - الخميس: 9:00 - 20:00",
        }
        for key, value in default_settings.items():
            db.add(Setting(key=key, value=value))

        db.commit()
        print("Database seeded successfully!")
        print(f"  - 2 Roles (admin, customer)")
        print(f"  - 1 Admin user (admin@alquds-store.com / admin123456)")
        print(f"  - 3 Categories")
        print(f"  - 12 Products with images")
        print(f"  - 3 Pages")
        print(f"  - 9 Settings")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
