
import os
import uuid
import secrets
from datetime import datetime
from flask import (
    render_template,
    url_for,
    flash,
    redirect,
    request,
    abort,
    jsonify,
)

from app import app, db, bcrypt

from app.forms import (
    RegistrationForm,
    LoginForm,
    ReviewForm,
    JobForm,
    ApplicationForm,
)

from app.models import User, Jobs, Review, Application

from flask_login import (
    login_user,
    current_user,
    logout_user,
    login_required,
)

from werkzeug.utils import secure_filename
from sqlalchemy.orm import joinedload

from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import VideoGrant

# --------------------------------------------------
# REVIEW DATA
# --------------------------------------------------

rev = [
    {
        "username": "Michael Scott",
        "review": "I hired multiple people using this website. Thank you",
    },
    {
        "username": "Dwight Schrute",
        "review": "It could be better",
    },
    {
        "username": "Andy Bernard",
        "review": "Best website ever",
    },
]

Random_Review = rev


def save_picture(form_picture):
    """Save an uploaded resume using a safe, unique filename."""

    if not form_picture or not form_picture.filename:
        raise ValueError("Please select a resume file.")

    original_name = secure_filename(form_picture.filename)

    if not original_name:
        raise ValueError("Invalid filename.")

    _, extension = os.path.splitext(original_name)
    extension = extension.lower()

    allowed_extensions = {
        ".pdf", ".jpg", ".jpeg", ".png", ".bmp", ".doc", ".docx"
    }

    if extension not in allowed_extensions:
        raise ValueError(
            "Allowed resume formats: PDF, JPG, JPEG, PNG, BMP, DOC, DOCX."
        )

    upload_folder = os.path.join(app.root_path, "static")
    os.makedirs(upload_folder, exist_ok=True)

    filename = secrets.token_hex(16) + extension
    file_path = os.path.join(upload_folder, filename)

    try:
        form_picture.save(file_path)
    except Exception:
        if os.path.exists(file_path):
            os.remove(file_path)
        app.logger.exception("Failed to save uploaded resume.")
        raise ValueError("Could not save the resume. Please try again.")

    return filename



# --------------------------------------------------
# REGISTER
# --------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        if current_user.usertype == "Job Seeker":
            return redirect(url_for("show_jobs"))
        if current_user.usertype == "Company":
            return redirect(url_for("posted_jobs"))

    form = RegistrationForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(
            email=form.email.data
        ).first()

        if existing_user:
            flash("An account with this email already exists.", "danger")
            return render_template(
                "register.html",
                form=form,
                Random_Review=Random_Review,
            )

        hashed_password = bcrypt.generate_password_hash(
            form.password.data
        ).decode("utf-8")

        user = User(
            username=form.username.data,
            usertype=form.usertype.data,
            email=form.email.data,
            password=hashed_password,
        )

        db.session.add(user)
        db.session.commit()

        flash(
            "Your account has been created! You can now log in.",
            "success",
        )
        return redirect(url_for("login"))

    return render_template(
        "register.html",
        form=form,
        Random_Review=Random_Review,
    )


# --------------------------------------------------
# LOGIN
# --------------------------------------------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.usertype == "Job Seeker":
            return redirect(url_for("show_jobs"))
        if current_user.usertype == "Company":
            return redirect(url_for("posted_jobs"))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(
            email=form.email.data
        ).first()

        if (
            user
            and bcrypt.check_password_hash(
                user.password, form.password.data
            )
            and user.usertype == form.usertype.data
        ):
            login_user(user, remember=form.remember.data)

            # Accept only local application paths for redirects.
            next_page = request.args.get("next")

            if next_page and next_page.startswith("/") and not next_page.startswith("//"):
                return redirect(next_page)

            if user.usertype == "Company":
                return redirect(url_for("posted_jobs"))

            return redirect(url_for("show_jobs"))

        flash(
            "Login unsuccessful. Check your email, password, and account type.",
            "danger",
        )

    return render_template(
        "login.html",
        form=form,
        Random_Review=Random_Review,
    )


# --------------------------------------------------
# LOGOUT
# --------------------------------------------------

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("show_jobs"))



# --------------------------------------------------
# APPLY FOR A JOB / UPLOAD RESUME
# --------------------------------------------------

@app.route("/post_cvs/<int:jobid>", methods=["GET", "POST"])
@login_required
def post_cvs(jobid):
    if current_user.usertype != "Job Seeker":
        abort(403)

    form = ApplicationForm()

    job = db.session.get(Jobs, jobid)

    if not job:
        flash("This job could not be found.", "danger")
        return redirect(url_for("show_jobs"))

    if form.validate_on_submit():
        uploaded_file = form.cv.data

        if not uploaded_file or not uploaded_file.filename:
            flash("Please select a resume file.", "danger")
            return render_template(
                "post_cvs.html",
                form=form,
                Random_Review=Random_Review,
            )

        saved_filename = None

        try:
            # Save the uploaded resume.
            saved_filename = save_picture(uploaded_file)

            # Create the application with valid model relationships.
            application = Application(
                gender=form.gender.data,
                degree=form.degree.data,
                industry=form.industry.data,
                experience=form.experience.data,
                cover_letter=form.cover_letter.data,
                application_submiter=current_user,
                job=job,
                cv=saved_filename,
                status="Pending",
                interview_enabled=False,
                interview_datetime=None,
            )

            db.session.add(application)
            db.session.commit()

            flash(
                "Your application has been submitted successfully!",
                "success",
            )

            return redirect(url_for("my_applications"))

        except Exception:
            db.session.rollback()

            # Remove the uploaded file if the database operation fails.
            if saved_filename:
                file_path = os.path.join(
                    app.root_path,
                    "static",
                    saved_filename,
                )

                if os.path.isfile(file_path):
                    try:
                        os.remove(file_path)
                    except OSError:
                        app.logger.exception(
                            "Could not remove the uploaded resume."
                        )

            app.logger.exception("Failed to submit job application")

            flash(
                "Unable to submit your application. "
                "Please check the resume and try again.",
                "danger",
            )

    return render_template(
        "post_cvs.html",
        form=form,
        Random_Review=Random_Review,
    )


# --------------------------------------------------
# POST A JOB
# --------------------------------------------------

@app.route("/post_jobs", methods=["GET", "POST"])
@login_required
def post_jobs():
    if current_user.usertype != "Company":
        abort(403)

    form = JobForm()

    if form.validate_on_submit():
        job = Jobs(
            title=form.title.data,
            industry=form.industry.data,
            description=form.description.data,
            job_applier=current_user,
        )

        db.session.add(job)
        db.session.commit()

        flash("Job posted successfully!", "success")
        return redirect(url_for("posted_jobs"))

    return render_template(
        "post_jobs.html",
        form=form,
        Random_Review=Random_Review,
    )


# --------------------------------------------------
# POST A REVIEW
# --------------------------------------------------


@app.route("/review", methods=["GET", "POST"])
@login_required
def review():
    form = ReviewForm()

    if form.validate_on_submit():
        username = current_user.username
        review_text = form.review.data.strip()

        if not review_text:
            flash("Please enter your review.", "danger")
            return render_template(
                "review.html",
                form=form,
                Random_Review=Random_Review,
            )

        try:
            # Find an existing review by this username.
            existing_review = Review.query.filter_by(
                username=username
            ).first()

            if existing_review:
                # Update the existing review instead of inserting a duplicate.
                existing_review.review = review_text
                message = "Your review has been updated successfully!"
            else:
                # Create a review if this user has not submitted one.
                new_review = Review(
                    username=username,
                    review=review_text,
                )
                db.session.add(new_review)
                message = "Your review has been submitted successfully!"

            db.session.commit()
            flash(message, "success")
            return redirect(url_for("show_jobs"))

        except Exception:
            db.session.rollback()
            app.logger.exception("Failed to save review")
            flash(
                "Unable to save your review. Please try again.",
                "danger",
            )

    return render_template(
        "review.html",
        form=form,
        Random_Review=Random_Review,
    )

# --------------------------------------------------
# COMPANY'S POSTED JOBS
# --------------------------------------------------

@app.route("/posted_jobs")
@login_required
def posted_jobs():
    if current_user.usertype != "Company":
        abort(403)

    jobs = Jobs.query.filter_by(
        job_applier=current_user
    ).all()

    return render_template(
        "show_jobs.html",
        jobs=jobs,
        Random_Review=Random_Review,
    )


# --------------------------------------------------
# VIEW APPLICATIONS FOR A JOB
# --------------------------------------------------

@app.route("/show_applications/<int:jobid>", methods=["GET"])
@login_required
def show_applications(jobid):
    if current_user.usertype != "Company":
        abort(403)

    job = db.session.get(Jobs, jobid)

    if not job:
        abort(404)

    # A company can view applicants only for its own job.
    if job.job_applier != current_user:
        abort(403)

    applications = (
        Application.query
        .filter_by(job_id=jobid)
        .order_by(
            Application.degree,
            Application.experience.desc(),
        )
        .all()
    )

    return render_template(
        "show_applications.html",
        applications=applications,
        Random_Review=Random_Review,
    )

@app.route("/my_applications", methods=["GET"])
@login_required
def my_applications():
    if current_user.usertype != "Job Seeker":
        abort(403)

    applications = (
        Application.query
        .filter_by(user_id=current_user.id)
        .order_by(Application.id.desc())
        .all()
    )

    return render_template(
        "my_applications.html",
        applications=applications,
        Random_Review=Random_Review,
    )


@app.route(
    "/update_application_status/<int:application_id>",
    methods=["POST"]
)
@login_required
def update_application_status(application_id):

    # Only companies can update application statuses.
    if current_user.usertype != "Company":
        abort(403)

    application = db.session.get(Application, application_id)

    if not application:
        abort(404)

    # Verify that the company owns the job.
    job = db.session.get(Jobs, application.job_id)

    if not job or job.job_applier != current_user:
        abort(403)

    allowed_statuses = [
        "Pending",
        "Shortlisted",
        "Rejected",
        "Hired",
    ]

    new_status = request.form.get("status", "").strip()

    if new_status not in allowed_statuses:
        flash("Invalid application status.", "danger")
        return redirect(
            url_for(
                "show_applications",
                jobid=application.job_id
            )
        )

    try:
        application.status = new_status
        db.session.commit()

        flash(
            f"Application status updated to {new_status}.",
            "success"
        )

    except Exception:
        db.session.rollback()
        app.logger.exception("Failed to update application status")
        flash("Could not update application status.", "danger")

    return redirect(
        url_for(
            "show_applications",
            jobid=application.job_id
        )
    )

# --------------------------------------------------
# SCHEDULE AN INTERVIEW
# --------------------------------------------------

@app.route(
    "/schedule_interview/<int:application_id>",
    methods=["POST"]
)
@login_required
def schedule_interview(application_id):

    # Only companies can schedule interviews.
    if current_user.usertype != "Company":
        abort(403)

    application = db.session.get(Application, application_id)

    if not application:
        abort(404)

    # Verify that the company owns the job.
    job = db.session.get(Jobs, application.job_id)

    if not job or job.job_applier != current_user:
        abort(403)

    interview_date = request.form.get(
        "interview_datetime", ""
    ).strip()

    if not interview_date:
        flash("Please select an interview date and time.", "danger")
        return redirect(
            url_for(
                "show_applications",
                jobid=application.job_id
            )
        )

    try:
        interview_datetime = datetime.strptime(
            interview_date,
            "%Y-%m-%dT%H:%M"
        )

        if interview_datetime <= datetime.now():
            flash(
                "Interview date and time must be in the future.",
                "danger"
            )
            return redirect(
                url_for(
                    "show_applications",
                    jobid=application.job_id
                )
            )

        application.interview_enabled = True
        application.interview_datetime = interview_datetime

        db.session.commit()

        flash(
            "Interview scheduled successfully.",
            "success"
        )

    except ValueError:
        flash("Invalid interview date and time.", "danger")

    except Exception:
        db.session.rollback()
        app.logger.exception("Failed to schedule interview")
        flash("Could not schedule the interview.", "danger")

    return redirect(
        url_for(
            "show_applications",
            jobid=application.job_id
        )
    )

# --------------------------------------------------
# INTERVIEW PAGE
# --------------------------------------------------

# --------------------------------------------------
# INTERVIEW PAGE
# --------------------------------------------------

@app.route("/meeting/<int:application_id>")
@login_required
def meeting(application_id):
    application = db.session.get(Application, application_id)

    if not application:
        abort(404)

    # Allow only the company that owns the job
    # or the job seeker who submitted this application.
    if current_user.usertype == "Company":
        job = db.session.get(Jobs, application.job_id)

        if not job or job.job_applier != current_user:
            abort(403)

    elif current_user.usertype == "Job Seeker":
        if application.user_id != current_user.id:
            abort(403)

    else:
        abort(403)

    # Do not allow access before the interview is scheduled.
    if not application.interview_enabled or not application.interview_datetime:
        flash("This interview has not been scheduled yet.", "warning")

        if current_user.usertype == "Job Seeker":
            return redirect(url_for("my_applications"))

        return redirect(
            url_for("show_applications", jobid=application.job_id)
        )

    applicant = db.session.get(User, application.user_id)

    return render_template(
        "meeting.html",
        application_id=application.id,
        applicant=applicant,
        Random_Review=Random_Review,
    )

# --------------------------------------------------
# SHOW ALL JOBS
# --------------------------------------------------

@app.route("/")
@app.route("/show_jobs")
def show_jobs():
    jobs = Jobs.query.all()

    return render_template(
        "show_jobs.html",
        jobs=jobs,
        Random_Review=Random_Review,
    )


# --------------------------------------------------
# VIEW RESUME
# --------------------------------------------------

@app.route("/resume/<int:id>", methods=["GET"])
@login_required
def resume(id):
    application = db.session.get(Application, id)

    if not application:
        abort(404)

    if current_user.usertype == "Company":
        job = db.session.get(Jobs, application.job_id)

        if not job or job.job_applier != current_user:
            abort(403)

    elif current_user.usertype == "Job Seeker":
        if application.user_id != current_user.id:
            abort(403)

    else:
        abort(403)

    return render_template(
        "resume.html",
        cv=application.cv,
        Random_Review=Random_Review,
        id=id,
    )

@app.route("/dashboard")
@login_required
def dashboard():
    if current_user.usertype != "Company":
        abort(403)

    jobs = Jobs.query.filter_by(
        user_id=current_user.id
    ).all()

    job_ids = [job.id for job in jobs]

    if job_ids:
        applications = Application.query.filter(
            Application.job_id.in_(job_ids)
        ).all()
    else:
        applications = []

    total_applications = len(applications)

    pending_count = sum(
        1 for application in applications
        if application.status == "Pending"
    )

    shortlisted_count = sum(
        1 for application in applications
        if application.status == "Shortlisted"
    )

    rejected_count = sum(
        1 for application in applications
        if application.status == "Rejected"
    )

    hired_count = sum(
        1 for application in applications
        if application.status == "Hired"
    )

    return render_template(
        "dashboard.html",
        total_applications=total_applications,
        pending_count=pending_count,
        shortlisted_count=shortlisted_count,
        rejected_count=rejected_count,
        hired_count=hired_count,
        jobs=jobs,
        Random_Review=Random_Review,
    )
@app.route("/video/token", methods=["POST"])
@login_required
def video_token():
    if current_user.usertype not in ["Company", "Job Seeker"]:
        return jsonify({"error": "Unauthorized"}), 403

    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    api_key = os.getenv("TWILIO_API_KEY")
    api_secret = os.getenv("TWILIO_API_SECRET")

    if not all([account_sid, api_key, api_secret]):
        app.logger.error("Twilio credentials are not configured.")
        return jsonify({
            "error": "Twilio credentials are not configured on the server."
        }), 500

    data = request.get_json(silent=True) or {}
    room_name = str(data.get("room", "")).strip()

    # A room name must be shared by both interview participants.
    if not room_name:
        return jsonify({
            "error": "A shared interview room name is required."
        }), 400

    try:
        token = AccessToken(
            account_sid,
            api_key,
            api_secret,
            identity=f"user-{current_user.id}-{uuid.uuid4().hex[:8]}"
        )

        token.add_grant(VideoGrant(room=room_name))

        return jsonify({
            "token": token.to_jwt(),
            "room": room_name
        })

    except Exception:
        app.logger.exception("Failed to generate Twilio video token.")
        return jsonify({
            "error": "Could not  create the interview token."
        }), 500