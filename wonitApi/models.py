# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.utils.timezone import now

class AuthGroup(models.Model):
    name = models.CharField(unique=True, max_length=150)

    class Meta:
        managed = False
        db_table = 'auth_group'


class AuthGroupPermissions(models.Model):
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)
    permission = models.ForeignKey('AuthPermission', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_group_permissions'
        unique_together = (('group', 'permission'),)


class AuthPermission(models.Model):
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING)
    codename = models.CharField(max_length=100)
    name = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = 'auth_permission'
        unique_together = (('content_type', 'codename'),)


class AuthUser(models.Model):
    password = models.CharField(max_length=128)
    last_login = models.DateTimeField(blank=True, null=True)
    is_superuser = models.BooleanField()
    username = models.CharField(unique=True, max_length=150)
    last_name = models.CharField(max_length=150)
    email = models.CharField(max_length=254)
    is_staff = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateTimeField()
    first_name = models.CharField(max_length=150)
    def __str__(self):
        return f"{self.username}"

    class Meta:
        managed = False
        db_table = 'auth_user'


class AuthUserGroups(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    group = models.ForeignKey(AuthGroup, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_groups'
        unique_together = (('user', 'group'),)


class AuthUserUserPermissions(models.Model):
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    permission = models.ForeignKey(AuthPermission, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'auth_user_user_permissions'
        unique_together = (('user', 'permission'),)


class DjangoAdminLog(models.Model):
    object_id = models.TextField(blank=True, null=True)
    object_repr = models.CharField(max_length=200)
    action_flag = models.PositiveSmallIntegerField()
    change_message = models.TextField()
    content_type = models.ForeignKey('DjangoContentType', models.DO_NOTHING, blank=True, null=True)
    user = models.ForeignKey(AuthUser, models.DO_NOTHING)
    action_time = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_admin_log'


class DjangoContentType(models.Model):
    app_label = models.CharField(max_length=100)
    model = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'django_content_type'
        unique_together = (('app_label', 'model'),)


class DjangoMigrations(models.Model):
    app = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    applied = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_migrations'


class DjangoSession(models.Model):
    session_key = models.CharField(primary_key=True, max_length=40)
    session_data = models.TextField()
    expire_date = models.DateTimeField()

    class Meta:
        managed = False
        db_table = 'django_session'


class Games(models.Model):
    game_id = models.AutoField(primary_key=True)
    league = models.TextField()
    team1 = models.TextField()
    team2 = models.TextField()
    prediction = models.TextField()
    prediction_type = models.TextField()
    result = models.CharField(max_length=450)
    odd = models.CharField(max_length=450)
    matchday = models.DateField(default=now())
    time_created = models.TimeField(default=now())
    date_created = models.DateField(default=now())
    game_type = models.CharField(max_length=250)

    def __str__(self):
        return f"{self.team1} vs {self.team2}"

    class Meta:
        managed = True
        db_table = 'games'


class BookingCode(models.Model):
    bc_id = models.AutoField(primary_key=True)
    sportyBet_code = models.CharField(max_length=250,default="")
    betWay_code = models.CharField(max_length=250,default="")


    def __str__(self):
        return f"SportyBet: {self.sportyBet_code}\n BetWay: {self.betWay_code}"
    class Meta:
        managed = True
        db_table = 'BookingCode'


class Slips(models.Model):
    slip_id = models.AutoField(primary_key=True)
    games = models.ManyToManyField(Games,related_name='slips')
    results = models.TextField()
    total_odd = models.CharField()
    price = models.DecimalField(decimal_places=2,max_digits=1000)
    booking_code = models.ForeignKey(BookingCode,on_delete=models.DO_NOTHING)
    match_day = models.DateField(default=now)
    start_time = models.TimeField(default=now)
    CATEGORY_CHOICES = [
        ('free', 'Free'),
        ('vvip1', 'DAILY VVIP PLAN'),
        ('vvip2','DAILY VVIP PLAN 2'),
        ('vvip3','DAILY VVIP PLAN 3'),
        ('vip','VIP PLAN')
    ]

    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES,default="")
    date_created = models.DateField()


    class Meta:
        managed = True
        db_table = 'Slips'


class Purchase(models.Model):
    purchase_id = models.AutoField(primary_key=True)
    reference = models.CharField(default='233')
    user = models.ForeignKey(AuthUser,on_delete=models.DO_NOTHING)
    slip = models.ForeignKey(Slips,on_delete=models.DO_NOTHING)
    purchase_date = models.DateField(auto_now=True)

    class Meta:
        managed = True
        db_table = 'Purchases'

class Notifications(models.Model):
    notification_id = models.AutoField(primary_key=True)
    title = models.TextField()
    body = models.TextField()
    notification_date = models.DateField(auto_now=True)
    seen = models.BooleanField(default=False)
    cleared = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.message} on {self.notification_date}"

    class Meta:
        managed=True
        db_table = 'Notifications'


