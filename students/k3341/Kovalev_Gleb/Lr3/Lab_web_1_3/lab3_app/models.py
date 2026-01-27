from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q
from django.conf import settings


class Hotel(models.Model):
    id_hotel = models.AutoField(primary_key=True, db_column="id_hotel")
    city = models.CharField(max_length=30)
    name = models.CharField(max_length=30)
    num_of_rooms = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    address = models.CharField(max_length=50)
    image = models.ImageField(upload_to="hotels/", blank=True, null=True)

    class Meta:
        db_table = 'Hotel'

    def __str__(self) -> str:
        return f"{self.name} ({self.city})"


class TypeOfRoom(models.Model):
    id_type = models.AutoField(primary_key=True, db_column="id_type")
    name = models.CharField(max_length=30, unique=True)
    num_of_rooms = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    num_of_places = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    base_price = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    num_of_free_rooms = models.PositiveIntegerField(validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to="room_types/", blank=True, null=True)

    conveniences = models.ManyToManyField(
        "Convenience",
        through="ConvenienceType",
        related_name="room_types",
        blank=True,
    )

    class Meta:
        db_table = 'TypeOfRoom'
        constraints = [
            models.CheckConstraint(
                check=Q(num_of_free_rooms__lte=F("num_of_rooms")),
                name="chk_type_free_rooms_lte_total",
            )
        ]

    def __str__(self) -> str:
        return self.name


class Convenience(models.Model):
    id_convenience = models.AutoField(primary_key=True, db_column="id_convenience")
    name = models.CharField(max_length=30, unique=True)
    description = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        db_table = 'Convenience'

    def __str__(self) -> str:
        return self.name


class ConvenienceType(models.Model):
    id_convienienceAndType = models.AutoField(primary_key=True, db_column="id_convienienceAndType")

    convenience = models.ForeignKey(
        Convenience,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="id_concenience",
        related_name="convenience_types",
    )
    room_type = models.ForeignKey(
        TypeOfRoom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="id_type",
        related_name="convenience_types",
    )
    num = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'ConvienenceType'
        constraints = [
            models.UniqueConstraint(
                fields=["convenience", "room_type"],
                name="uq_convenience_room_type",
            )
        ]


class ContractNumber(models.Model):
    CONTRACT_TYPES = [
        ("Постоянный", "Постоянный"),
        ("Сезонный", "Сезонный"),
    ]

    contract_number = models.IntegerField(primary_key=True, db_column="contract_number")
    beginning_of_contract = models.DateField()
    end_of_contract = models.DateField()
    number_of_job_days = models.PositiveIntegerField(validators=[MaxValueValidator(31)])
    type_of_contract = models.CharField(max_length=10, choices=CONTRACT_TYPES)
    conditions = models.CharField(max_length=150, blank=True, null=True)

    class Meta:
        db_table = 'ContractNumber'
        constraints = [
            models.CheckConstraint(
                check=Q(beginning_of_contract__lte=F("end_of_contract")),
                name="chk_contract_begin_le_end",
            )
        ]

    def __str__(self) -> str:
        return f"#{self.contract_number} ({self.type_of_contract})"


class Staff(models.Model):
    JOB_TITLES = [
        ("Администратор", "Администратор"),
        ("Уборщик", "Уборщик"),
        ("Техник", "Техник"),
        ("Охранник", "Охранник"),
    ]

    id_staff = models.AutoField(primary_key=True, db_column="id_staff")
    contract = models.ForeignKey(
        ContractNumber,
        on_delete=models.PROTECT,
        db_column="contract_number",
        related_name="staff_members",
    )
    full_name = models.CharField(max_length=150)
    job_title = models.CharField(max_length=30, choices=JOB_TITLES)

    class Meta:
        db_table = 'Staff'

    def __str__(self) -> str:
        return f"{self.full_name} — {self.job_title}"


class Client(models.Model):
    id_client = models.AutoField(primary_key=True, db_column="id_client")
    name = models.CharField(max_length=30)
    surname = models.CharField(max_length=30)
    fathers_name = models.CharField(max_length=30, blank=True, null=True)
    home_adress = models.CharField(max_length=150)  # в дампе именно "home_adress"
    mobile_number = models.CharField(max_length=20)
    email = models.EmailField(max_length=30)

    class Meta:
        db_table = 'Client'

    def __str__(self) -> str:
        return f"{self.surname} {self.name}"


class RoomInHotel(models.Model):
    STATUSES = [
        ("Свободен", "Свободен"),
        ("Занят", "Занят"),
    ]

    id_number = models.AutoField(primary_key=True, db_column="id_number")
    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.PROTECT,
        db_column="id_hotel",
        related_name="rooms",
    )
    room_type = models.ForeignKey(
        TypeOfRoom,
        on_delete=models.PROTECT,
        db_column="id_type",
        related_name="rooms",
    )
    room_number = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    places_number = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=8, choices=STATUSES)
    cleaned = models.BooleanField(null=True, blank=True)

    class Meta:
        db_table = 'RoomInHotel'
        constraints = [
            models.UniqueConstraint(
                fields=["room_number", "hotel"],
                name="uq_room_number_per_hotel",
            )
        ]

    def __str__(self) -> str:
        return f"{self.hotel.name} #{self.room_number} ({self.places_number} мест)"


class DiscountOnTypeOfRoom(models.Model):
    id_discount = models.AutoField(primary_key=True, db_column="id_discount")
    name = models.CharField(max_length=30)
    description = models.CharField(max_length=150, blank=True, null=True)
    percent_of_discount = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    date_start_of_discount = models.DateField()
    date_end_of_discount = models.DateField()
    room_type = models.ForeignKey(
        TypeOfRoom,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="type_Of_Room",
        related_name="discounts",
    )

    class Meta:
        db_table = 'DiscountOnTypeOfRoom'
        constraints = [
            models.CheckConstraint(
                check=Q(date_start_of_discount__lte=F("date_end_of_discount")),
                name="chk_discount_start_le_end",
            )
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.percent_of_discount}%)"


class Booking(models.Model):
    STATUSES = [
        ("Забронирован", "Забронирован"),
        ("Заселен", "Заселен"),
        ("Ожидает оплату", "Ожидает оплату"),
        ("Выселен", "Выселен"),
        ("Отменен", "Отменен"),
    ]
    PAY_TYPES = [
        ("Наличные", "Наличные"),
        ("Карта", "Карта"),
        ("СБП", "СБП"),
    ]

    id_book = models.AutoField(primary_key=True, db_column="id_book")
    book_status = models.CharField(max_length=14, choices=STATUSES)
    date_start = models.DateField()
    date_end = models.DateField()

    client = models.ForeignKey(Client, on_delete=models.PROTECT, db_column="id_client", related_name="bookings")
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, db_column="id_staff", related_name="bookings")
    room_type = models.ForeignKey(TypeOfRoom, on_delete=models.PROTECT, db_column="id_type", related_name="bookings")

    price = models.DecimalField(max_digits=9, decimal_places=2)
    payed = models.DecimalField(max_digits=9, decimal_places=2, validators=[MinValueValidator(0)])
    type_of_payment = models.CharField(max_length=8, choices=PAY_TYPES)

    additional_conveniences = models.ManyToManyField(
        Convenience,
        through="BookingConvenience",
        related_name="bookings_with_extra",
        blank=True,
    )

    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.PROTECT,
        db_column="id_hotel",
        related_name="bookings",
        null=True,
        blank=True,
    )

    class Meta:
        db_table = 'BookOfHotel'
        constraints = [
            models.CheckConstraint(check=Q(date_start__lte=F("date_end")), name="chk_booking_start_le_end"),
            models.CheckConstraint(check=Q(payed__lte=F("price")), name="chk_booking_payed_lte_price"),
        ]

    def __str__(self) -> str:
        return f"Booking #{self.id_book} ({self.book_status})"

class RoomTypeAvailability(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE, related_name="room_type_availability")
    room_type = models.ForeignKey(TypeOfRoom, on_delete=models.CASCADE, related_name="availability_days")
    day = models.DateField()
    free_rooms = models.PositiveIntegerField(validators=[MinValueValidator(0)])

    class Meta:
        db_table = "RoomTypeAvailability"
        constraints = [
            models.UniqueConstraint(fields=["hotel", "room_type", "day"], name="uq_hotel_type_day"),
        ]

    def __str__(self):
        return f"{self.hotel.name} {self.room_type.name} {self.day} free={self.free_rooms}"


class BookingConvenience(models.Model):
    id = models.BigAutoField(primary_key=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="booking_conveniences")
    convenience = models.ForeignKey(Convenience, on_delete=models.PROTECT, related_name="booking_conveniences")

    class Meta:
        db_table = "BookingConvenience"
        constraints = [
            models.UniqueConstraint(fields=["booking", "convenience"], name="uq_booking_convenience")
        ]


class CheckIn(models.Model):
    id_check_in = models.AutoField(primary_key=True, db_column="id_check_in")
    date_check_in = models.DateField()
    date_check_out = models.DateField()

    client = models.ForeignKey(Client, on_delete=models.PROTECT, db_column="id_client", related_name="checkins")
    room = models.ForeignKey(RoomInHotel, on_delete=models.PROTECT, db_column="id_room", related_name="checkins")
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, db_column="id_staff", related_name="checkins")
    booking = models.ForeignKey(Booking, on_delete=models.PROTECT, db_column="id_book", related_name="checkins")

    class Meta:
        db_table = 'CheckIn'
        constraints = [
            models.CheckConstraint(check=Q(date_check_in__lte=F("date_check_out")), name="chk_checkin_in_le_out")
        ]

    def __str__(self) -> str:
        return f"CheckIn #{self.id_check_in}"


class CleaningTime(models.Model):
    STATUSES = [
        ("Убран", "Убран"),
        ("Не убран", "Не убран"),
    ]

    id_cleaning = models.AutoField(primary_key=True, db_column="id_cleaning")
    room = models.ForeignKey(RoomInHotel, on_delete=models.PROTECT, db_column="id_room", related_name="cleanings")
    staff = models.ForeignKey(Staff, on_delete=models.PROTECT, db_column="id_staff", related_name="cleanings")
    cleaning_time = models.TimeField()
    date = models.DateField()
    cleaning_status = models.CharField(max_length=8, choices=STATUSES)

    class Meta:
        db_table = 'CleaningTime'
        constraints = [
            models.UniqueConstraint(fields=["room", "date"], name="uq_cleaning_room_date")
        ]

    def __str__(self) -> str:
        return f"Cleaning #{self.id_cleaning} ({self.date})"

class Profile(models.Model):
    class Role(models.TextChoices):
        CLIENT = "client", "Client"
        ADMIN = "admin", "Admin"
        CLEANER = "cleaner", "Cleaner"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CLIENT)

    hotel = models.ForeignKey(Hotel, on_delete=models.PROTECT, null=True, blank=True, related_name="profiles")
    client = models.OneToOneField(Client, on_delete=models.SET_NULL, null=True, blank=True, related_name="profile")

    staff = models.OneToOneField(
        "Staff",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profile",
    )

    def __str__(self):
        return f"{self.user.username} ({self.role})"