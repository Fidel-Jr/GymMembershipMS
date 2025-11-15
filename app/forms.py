# -----------------------
# Edit Member Form
# -----------------------
from wtforms import BooleanField
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, FloatField, SelectField, DateField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from app.models import MembershipPlan, User
from flask_wtf.file import FileField, FileAllowed

# -----------------------
# Login Form
# -----------------------
class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=100)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    submit = SubmitField('Login')


# -----------------------
# Member Registration Form (Admin Use)
# -----------------------
class RegisterForm(FlaskForm):
    fullname = StringField("Full Name", validators=[DataRequired(), Length(min=3, max=100)])
    username = StringField("Username", validators=[DataRequired(), Length(min=3, max=50)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField("Confirm Password", validators=[
        DataRequired(),
        EqualTo("password", message="Passwords must match.")
    ])
    submit = SubmitField("Register")

class MembershipPlanForm(FlaskForm):
    name = StringField('Plan Name', validators=[DataRequired(), Length(max=100)])
    features = StringField('Features (comma-separated)', validators=[DataRequired()])
    price = FloatField('Price', validators=[DataRequired()])
    duration_months = SelectField('Duration (Months)', choices=[('1', '1'), ('3', '3'), ('6', '6'), ('12', '12')], validators=[DataRequired()])
    status = SelectField(
        'Status',
        choices=[('', 'Select Status'), ('available', 'Available'), ('unavailable', 'Unavailable')],
        default='available',
        validators=[]
    )
    submit = SubmitField('Save Membership Plan')
    

class AssignMembershipForm(FlaskForm):
    member_id = SelectField('Member', validators=[DataRequired()], coerce=int)
    plan_id = SelectField('Plan', validators=[DataRequired()], coerce=int)
    start_date = DateField('Start Date', validators=[DataRequired()])
    payment_method = SelectField(
        'Payment Method',
        choices=[('cash', 'Cash'), ('card', 'Credit/Debit Card'), ('bank', 'Bank Transfer')],
        validators=[DataRequired()]
    )
    submit = SubmitField('Assign Membership')

    def __init__(self, *args, **kwargs):
        super(AssignMembershipForm, self).__init__(*args, **kwargs)
        # ✅ Let Select2 AJAX handle this dynamically
        self.member_id.choices = []

        # ✅ Load plans normally
        self.plan_id.choices = [
            (p.id, f"{p.name} - ${int(p.price)}")
            for p in MembershipPlan.query.order_by(MembershipPlan.id).all()
        ]

# -----------------------
# Edit Membership Form
# -----------------------
class EditMembershipForm(FlaskForm):
    plan_id = SelectField('Plan', validators=[DataRequired()], coerce=int)
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    status = SelectField('Status', choices=[('active', 'Active'), ('expired', 'Expired')], validators=[DataRequired()])
    paymentMethod = SelectField('Payment Method', choices=[('cash', 'Cash'), ('card', 'Credit/Debit Card'), ('bank', 'Bank Transfer')], validators=[DataRequired()])
    submit = SubmitField('Save Changes')

    def __init__(self, *args, **kwargs):
        super(EditMembershipForm, self).__init__(*args, **kwargs)
        self.plan_id.choices = [
            (p.id, f"{p.name} - ${int(p.price)}") for p in MembershipPlan.query.order_by(MembershipPlan.id).all()
        ]
        
class MemberEditForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=3, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    contact_number = StringField('Phone', validators=[Length(max=20)])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('member', 'Member')])
    is_active = SelectField('Status', choices=[('1', 'Active'), ('0', 'Inactive')], default='1')
    image = FileField('Profile Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')])
    submit = SubmitField('Save Changes')


class ProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired(), Length(min=3, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    contact_number = StringField('Phone', validators=[Length(max=20)])
    role = SelectField('Role', choices=[('admin', 'Admin'), ('member', 'Member')])
    password = PasswordField('New Password (leave blank to keep current)', validators=[Length(min=0)])
    image = FileField('Profile Image', validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')])
    submit = SubmitField('Save Changes')