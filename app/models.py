
from app import db, login_manager
from datetime import datetime
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# --------------------------------------------------
# USER MODEL
# --------------------------------------------------

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    usertype = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

    # Jobs posted by this user (Company).
    jobs = db.relationship(
        "Jobs",
        backref="job_applier",
        lazy=True
    )

    # Applications submitted by this user (Job Seeker).
    applications = db.relationship(
        "Application",
        backref="application_submiter",
        lazy=True
    )

    def __repr__(self):
        return (
            f"User('{self.id}', '{self.username}', "
            f"'{self.usertype}', '{self.email}')"
        )


# --------------------------------------------------
# APPLICATION MODEL
# --------------------------------------------------

class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    gender = db.Column(db.String(20), nullable=False)

    date_posted = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    degree = db.Column(db.String(20), nullable=False)
    industry = db.Column(db.String(50), nullable=False)
    experience = db.Column(db.Integer, nullable=False)

    # Uploaded resume filename.
    cv = db.Column(db.String(255), nullable=False)

    cover_letter = db.Column(db.Text, nullable=False)

    # Application tracking status.
    status = db.Column(
        db.String(20),
        nullable=False,
        default="Pending"
    )

    # Interview scheduling fields.
    interview_enabled = db.Column(
        db.Boolean,
        nullable=False,
        default=False
    )

    interview_datetime = db.Column(
        db.DateTime,
        nullable=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    job_id = db.Column(
        db.Integer,
        db.ForeignKey("jobs.id"),
        nullable=False
    )

    # Relationship to the job this application belongs to.
    job = db.relationship(
        "Jobs",
        back_populates="applications",
        lazy=True
    )

    # Access the applicant through application.user.
    # This matches User.applications above.
   
    def __repr__(self):
        return (
            f"Application('{self.id}', "
            f"'{self.gender}', "
            f"'{self.date_posted}', "
            f"'{self.degree}', "
            f"'{self.industry}', "
            f"'{self.experience}', "
            f"'{self.status}', "
            f"'{self.user_id}', "
            f"'{self.job_id}')"
        )


# --------------------------------------------------
# JOB MODEL
# --------------------------------------------------

class Jobs(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title = db.Column(db.String(100), nullable=False)
    industry = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)

    date_posted = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    # Applications submitted for this job.
    applications = db.relationship(
        "Application",
        back_populates="job",
        lazy=True
    )

    def __repr__(self):
        return (
            f"Jobs('{self.id}', '{self.title}', "
            f"'{self.industry}', '{self.date_posted}')"
        )


# --------------------------------------------------
# REVIEW MODEL
# --------------------------------------------------

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(
        db.String(20),
        unique=True,
        nullable=False
    )

    review = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"Review('{self.username}', '{self.review}')"
