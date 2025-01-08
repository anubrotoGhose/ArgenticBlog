from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    send_file,
    jsonify,
    flash,
)
from datetime import datetime
from datetime import timezone
import os
from supabase import create_client, Client
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from bs4 import BeautifulSoup

load_dotenv()
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(supabase_url, supabase_key)


app = Flask(__name__)
app.secret_key = "your_secret_key"
UPLOAD_FOLDER = "static/profile_photos"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["UPLOAD_CONTENTS"] = "static/contents"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB


@app.route("/", methods=["GET", "POST"])
def home():
    response = (
        supabase.table("articles")
        .select("*")
        .order("PostTimeStamp", desc=True)
        .limit(10)  # Limit the results to the first 10
        .execute()
    )
    posts = response.data

    # Filter out invalid posts or set a default value for missing content
    if posts:
        for post in posts:
            # Set a default value for missing content
            content = post.get("content")
            if content is None:
                post["content"] = "No content available"
            else:
                # Parse the HTML content
                soup = BeautifulSoup(content, "html.parser")
                # Get text without HTML tags
                post["content"] = soup.get_text(separator=" ", strip=True)

    # print(posts)  # Debugging output
    if is_user_logged_in():
        email = session.get("user")  # Get the logged-in user's email

        # Fetch profile photo URL from the profiles table
        response = (
            supabase.table("profiles")
            .select("profile_photo")
            .eq("email", email)
            .single()
            .execute()
        )

        response_posts1 = (
            supabase.table("articles")
            .select("*")
            .order("PostTimeStamp", desc=True)
            .eq("email", email)
            .limit(10)  # Limit the results to the first 10
            .execute()
        )
        posts1 = response_posts1.data
        profile_photo_url = response.data["profile_photo"] if response.data else None
        if posts1:
            for post in posts1:
                # Set a default value for missing content
                content = post.get("content")
                if content is None:
                    post["content"] = "No content available"
                else:
                    # Parse the HTML content
                    soup = BeautifulSoup(content, "html.parser")
                    # Get text without HTML tags
                    post["content"] = soup.get_text(separator=" ", strip=True)
        # print(posts1)
        # header content with the profile photo
        header_content = f"""
        <header>
            <h1>Welcome to ArgenticBlog</h1>
            <p>Share your thoughts with the world</p>
            <div class="profile-photo">
                <img src="/{profile_photo_url}" alt="Profile Photo" class="profile-img">
                <div id="dropdown-menu" class="dropdown-menu">
                    <a href="/profile">Profile</a>
                    <a href="/logout">Logout</a>
            </div>
        </header>"""
        return render_template(
            "home.html", header_content=header_content, posts=posts, posts1=posts1
        )
    else:
        # print(session)
        header_content = """
        <header>
                <div class="links">
                    <a href="/login" class="header-link">Login</a> |
                    <a href="/signup" class="header-link">Sign Up</a>
                </div>
                <h1>Welcome to ArgenticBlog</h1>
                <p>Share your thoughts with the world</p>
            </header>"""
        return render_template("home.html", header_content=header_content, posts=posts)


@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query")

    if not query:
        return render_template(
            "search_results.html", posts=[], message="Please enter a search term."
        )

    response = (
        supabase.table("articles")
        .select("*")
        .or_(
            f"title.ilike.%{query}%,content.ilike.%{query}%"
        )  # Search in both title and content
        .order("PostTimeStamp", desc=True)  # Order by timestamp
        .execute()
    )
    posts = response.data
    if posts:
        for post in posts:
            # Set a default value for missing content
            content = post.get("content")
            if content is None:
                post["content"] = "No content available"
            else:
                # Parse the HTML content
                soup = BeautifulSoup(content, "html.parser")
                # Get text without HTML tags
                post["content"] = soup.get_text(separator=" ", strip=True)
    # Render the search results page
    return render_template("search_results.html", posts=posts)


@app.route("/search_author", methods=["GET"])
def search_author():
    query = request.args.get("query", "").strip()
    username = request.args.get("username", "").strip() 
    if not query:
        return render_template(
            "search_results.html", posts=[], message="Please enter a search term."
        )

    # Fetch articles matching the search query (title, content, or author username)
    response = (
        supabase.table("articles")
        .select("*")
        .or_(
            f"title.ilike.%{query}%,content.ilike.%{query}%"
        )
        .eq("username", username)
        .order("PostTimeStamp", desc=True)  # Order by timestamp
        .execute()
    )

    posts = response.data if response.data else []

    # Clean up the content in the search results
    for post in posts:
        content = post.get("content")
        if not content:
            post["content"] = "No content available"
        else:
            # Ensure content is a string before processing
            content_str = str(content)
            soup = BeautifulSoup(content_str, "html.parser")
            post["content"] = soup.get_text(separator=" ", strip=True)

    # Render the search results page
    return render_template("search_results.html", posts=posts)

@app.route("/posthistory")
def posthistory():
    if is_user_logged_in():
        email = session.get("user")
        response = (
            supabase.table("articles")
            .select("*")
            .eq("email", email)
            .order("PostTimeStamp", desc=True)
            .execute()
        )
        posts = response.data

        # Filter out invalid posts or set a default value for missing content
        if posts:
            for post in posts:
                # Set a default value for missing content
                content = post.get("content")
                if content is None:
                    post["content"] = "No content available"
                else:
                    # Parse the HTML content
                    soup = BeautifulSoup(content, "html.parser")
                    # Get text without HTML tags
                    post["content"] = soup.get_text(separator=" ", strip=True)

        # print(posts)  # Debugging output
        response = (
            supabase.table("profiles")
            .select("profile_photo")
            .eq("email", email)
            .single()
            .execute()
        )
        profile_photo_url = response.data["profile_photo"] if response.data else None

        # Generate the header content with the profile photo
        header_content = f"""
        <header>
            <h1>Post History</h1>
            <div class="profile-photo">
                <img src="/{profile_photo_url}" alt="Profile Photo" class="profile-img">
                <div id="dropdown-menu" class="dropdown-menu">
                    <a href="/profile">Profile</a>
                    <a href="/logout">Logout</a>
            </div>
        </header>"""
        return render_template(
            "post_history.html", posts=posts, header_content=header_content
        )
    else:
        return redirect(url_for("login"))


def is_user_logged_in():
    return "user" in session


from flask import jsonify, render_template, request, redirect, url_for
from datetime import datetime, timezone


@app.route("/postblog", methods=["GET", "POST"])
def postblog():
    if is_user_logged_in():
        email = session.get("user")
        response_header = (
            supabase.table("profiles")
            .select("profile_photo")
            .eq("email", email)
            .single()
            .execute()
        )
        profile_photo_url = (
            response_header.data["profile_photo"] if response_header.data else None
        )

        # Get current date and time
        current_datetime = datetime.now().strftime("%A, %B %d, %Y %I:%M %p")

        header_content = f"""
        <header>
            <p>
            <div class="links">
                <a href="/" class="header-link"><h1>ArgenticBlog</h1></a>
            </div>
            </p>
            <div class="datetime">{current_datetime}</div>
            <div class="profile-photo">
                <img src="/{profile_photo_url}" alt="Profile Photo" class="profile-img">
                <div id="dropdown-menu" class="dropdown-menu">
            </div>
        </header>"""

        if request.method == "POST":
            title = request.form.get("title")
            content = request.form.get("content")

            if not title or not content:
                return (
                    jsonify({"success": False, "error": "Title or content missing"}),
                    400,
                )

            # Process the data (save to database or similar)
            # print(f"Title: {title}")
            # print(f"Content: {content}")

            response = (
                supabase.table("profiles")
                .select("username")
                .eq("email", email)
                .single()
                .execute()
            )

            username = response.data["username"]
            response = (
                supabase.table("articles")
                .insert(
                    {
                        "content": content,
                        "email": email,
                        "username": username,
                        "title": title,
                        "PostTimeStamp": datetime.now(timezone.utc).isoformat(),
                        "commentidlist": [],
                        "ratings": 0,
                        "ratingsidlist": [],
                    }
                )
                .execute()
            )
            return (
                jsonify({"success": True, "message": "Post saved successfully!"}),
                200,
            )
        else:
            # print("Not posted")
            pass

        # If the method is GET, render the post form
    return render_template("postblog.html", header_content=header_content)


@app.route("/post/<int:post_id>")
def post_detail(post_id):
    # Fetch the article from Supabase using the provided post_id

    response = supabase.table("articles").select("*").eq("articleid", post_id).execute()

    # Check if the response contains data
    if not response.data:
        return "Post not found", 404

    post = response.data[0]

    # Handle cases where content might be None
    if post["content"] is None:
        post["content"] = "No content available"

    # Render the post detail template with the retrieved post data

    if is_user_logged_in():
        email = session.get("user")  # Get the logged-in user's email

        # Fetch profile photo URL from the profiles table
        response_profile = (
            supabase.table("profiles")
            .select("profile_photo")
            .eq("email", email)
            .single()
            .execute()
        )
        # print(response_profile)
        # Check if the response contains data
        if response_profile.data:
            profile_photo_url = response_profile.data["profile_photo"]
        else:
            print(
                "Error fetching profile photo:", response_profile.error
            )  # This will print the error if it exists
        #     profile_photo_url = None
        # print("Profile Photo URL:", profile_photo_url)

        # Generate the header content with the profile photo
        header_content = f"""
        <header>
            <a href="/" class="header-link"><h1>ArgenticBlog</h1></a>
            <div class="profile-photo">
                <img src="/{profile_photo_url or 'static/profile_photos/default_profile.webp'}" alt="Profile Photo" class="profile-img">
                <div id="dropdown-menu" class="dropdown-menu">
                    <a href="/profile">Profile</a>
                    <a href="/logout">Logout</a>
                </div>
            </div>
        </header>"""
        # print(header_content)
        return render_template("post_detail.html", post=post, header_content=header_content)
    else:
        header_content = """
        <header>
            <div class="links">
                <a href="/login" class="header-link">Login</a> |
                <a href="/signup" class="header-link">Sign Up</a>
            </div>
            <a href="/" class="header-link"><h1>ArgenticBlog</h1></a>
        </header>"""

        return render_template("post_detail.html", post=post, header_content=header_content)


@app.route("/author/<string:username>", methods=["GET", "POST"])
def author_articles(username):
    # Handle search functionality
    search_query = request.args.get("query", "").strip()
    if search_query:
        # Redirect to the search route with the query
        return redirect(url_for("search_author", query=search_query, username=username))
    # Fetch articles by the author from Supabase
    query = supabase.table("articles").select("*").eq("username", username)
    if search_query:
        query = (
            query.filter(
                f"title.ilike.%{search_query}%,content.ilike.%{search_query}%"
            )
        )
    
    response_profile_photo = (
        supabase.table("profiles")
        .select("profile_photo")
        .eq("username", username)
        .single()
        .execute()
    )
    author_photo_url = response_profile_photo.data["profile_photo"] if response_profile_photo.data else None

    articles = query.execute()
    if articles.data:
        for post in articles.data:
            # Set a default value for missing content
            content = post.get("content")
            if content is None:
                post["content"] = "No content available"
            else:
                # Parse the HTML content
                soup = BeautifulSoup(content, "html.parser")
                # Get text without HTML tags
                post["content"] = soup.get_text(separator=" ", strip=True)

    if is_user_logged_in():
        email = session.get("user")  # Get the logged-in user's email

        # Fetch profile photo URL from the profiles table
        response = (
            supabase.table("profiles")
            .select("profile_photo")
            .eq("email", email)
            .single()
            .execute()
        )
        profile_photo_url = response.data["profile_photo"] if response.data else None
        
        header_content = f"""
        <header>
            <a href="/" class="header-link"><h1>ArgenticBlog</h1></a>
            <div class="profile-photo">
                <img src="/{profile_photo_url}" alt="Profile Photo" class="profile-img">
                <div id="dropdown-menu" class="dropdown-menu">
                    <a href="/profile">Profile</a>
                    <a href="/logout">Logout</a>
            </div>
        </header>"""
        # print(profile_photo_url)
        return render_template(
            "author_articles.html",
            header_content=header_content,
            username=username,
            posts=articles.data if articles.data else [],
            search_query=search_query,
            author_photo_url=author_photo_url,
        )
    else:
        # print(session)
        header_content = """
        <header>
                <div class="links">
                    <a href="/login" class="header-link">Login</a> |
                    <a href="/signup" class="header-link">Sign Up</a>
                </div>
                <a href="/" class="header-link"><h1>ArgenticBlog</h1></a>
            </header>"""
        return render_template(
            "author_articles.html",
            header_content=header_content,
            username=username,
            posts=articles.data if articles.data else [],
            search_query=search_query,
            author_photo_url=author_photo_url,
        )


@app.route("/like_dislike", methods=["POST"])
def like_dislike():
    if is_user_logged_in():
        email = session.get("user")
        response_username = (
            supabase.table("profiles")
            .select("username")
            .eq("email", email)
            .single()
            .execute()
        )

        # Ensure username is retrieved
        if not response_username.data:
            return jsonify({"error": "Unable to fetch username"}), 500

        username = response_username.data["username"]
        data = request.json

        # Debugging: Log the received data
        # print("Received data:", data)

        # Ensure all required fields are present
        required_fields = ["username", "target_type", "target_id", "action"]
        missing_fields = [field for field in required_fields if not data.get(field)]

        if missing_fields:
            return (
                jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}),
                400,
            )

        # print("username = ", username)
        # print("username type = ", type(username))

        target_type = data.get("target_type")
        target_id = data.get("target_id")
        action = data.get("action")

        # Determine the correct table and column based on target type
        if target_type == "article":
            table = "articles"
            id_column = "articleid"
        elif target_type == "comment":
            table = "comments"
            id_column = "commentid"
        else:
            return jsonify({"error": "Invalid target type"}), 400

        # Fetch the current record
        response = (
            supabase.table(table)
            .select("*")
            .eq(id_column, target_id)
            .single()
            .execute()
        )

        if not response.data:
            return jsonify({"error": "Target not found"}), 404

        current_data = response.data
        liked_by = current_data.get("liked_by", [])  # List of users who liked
        disliked_by = current_data.get("disliked_by", [])  # List of users who disliked

        # Prevent duplicate actions
        if action == "like" and username in liked_by:
            return jsonify({"error": "You have already liked this item"}), 400
        if action == "dislike" and username in disliked_by:
            return jsonify({"error": "You have already disliked this item"}), 400

        # Update likes/dislikes
        likes = current_data.get("likes", 0)
        dislikes = current_data.get("dislikes", 0)

        if action == "like":
            if username in disliked_by:
                # Remove user from dislikes and adjust count
                disliked_by.remove(username)
                dislikes -= 1
            liked_by.append(username)
            likes += 1
        elif action == "dislike":
            if username in liked_by:
                # Remove user from likes and adjust count
                liked_by.remove(username)
                likes -= 1
            disliked_by.append(username)
            dislikes += 1
        else:
            return jsonify({"error": "Invalid action"}), 400

        # Update the table
        supabase.table(table).update(
            {
                "likes": likes,
                "dislikes": dislikes,
                "liked_by": liked_by,
                "disliked_by": disliked_by,
            }
        ).eq(id_column, target_id).execute()

        return jsonify({"success": True, "likes": likes, "dislikes": dislikes})
    else:
        return jsonify({"error": "User not logged in"}), 401


@app.route("/add_comment", methods=["POST"])
def add_comment():
    if is_user_logged_in():
        data = request.json
        # print("Received data:", data)  # Debugging

        articleid = data.get("articleid")
        username = data.get("username")
        content = data.get("content")

        if not articleid or not username or not content:
            missing_fields = [
                field
                for field, value in {
                    "articleid": articleid,
                    "username": username,
                    "content": content,
                }.items()
                if not value
            ]
            return (
                jsonify({"error": f"Missing fields: {', '.join(missing_fields)}"}),
                400,
            )

        # Insert the comment
        supabase.table("comments").insert(
            {
                "articleid": articleid,
                "username": username,
                "content": content,
                "likes": 0,
                "dislikes": 0,
            }
        ).execute()

        return jsonify({"success": True})


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        try:
            # Authenticate user with Supabase
            user = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            session["user"] = user.user.email  # Store user email in session
            flash("Login successful!", "success")
            return redirect(url_for("home"))
        except Exception as e:
            flash("Invalid email or password.", "danger")
            # print(e)

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]
        username = request.form["username"]
        password = request.form["password"]

        # Check if the username already exists in the 'profiles' table
        existing_username = (
            supabase.table("profiles")
            .select("username")
            .eq("username", username)
            .execute()
        )
        existing_useremail = (
            supabase.table("profiles").select("email").eq("email", email).execute()
        )
        # If the username already exists, show an error message
        if existing_username.data and existing_useremail.data:
            flash(
                "Username and email are already taken. Please choose a different one.",
                "danger",
            )
            return render_template(
                "signup.html",
                msg2="Username is already taken. Please choose a different one.",
                msg1="Email is already taken. Please choose a different one.",
            )
        elif existing_username.data:
            flash("Username is already taken. Please choose a different one.", "danger")
            return render_template(
                "signup.html",
                msg2="Username is already taken. Please choose a different one.",
            )
        elif existing_useremail.data:
            flash("Email is already in use. Please choose a different one.", "danger")
            return render_template(
                "signup.html",
                msg1="Email is already taken. Please choose a different one.",
            )

        else:
            # print("username and email is valid")
            # Insert a new record into the profiles table
            profile_response = (
                supabase.table("profiles")
                .insert(
                    {
                        "email": email,
                        "username": username,
                        "commentidlist": [],  # Initialize as empty list
                        "articleidlist": [],  # Initialize as empty list
                        "ratingsidlist": [],  # Initialize as empty list
                        "profile_photo": "static/profile_photos/default_profile.jpg",
                    }
                )
                .execute()
            )

            # print("Profile Insertion Response:", profile_response)
        try:
            # Register user with Supabase
            signup_response = supabase.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                }
            )

            # Handle the result of the profile insertion
            if profile_response.get("error"):
                flash(
                    f"Error creating profile: {profile_response['error']['message']}",
                    "danger",
                )
                return render_template("signup.html")

            flash("Signup successful! Please login.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Error during signup. Please try again. Error: {str(e)}", "danger")
            return render_template("signup.html")

    return render_template("signup.html")


@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if request.method == "POST":
        email = request.form["email"]
        old_password = request.form["old_password"]
        new_password = request.form["new_password"]

        try:
            # Step 1: Re-authenticate user with their current password
            user = supabase.auth.sign_in_with_password(
                {"email": email, "password": old_password}
            )

            # Step 2: Update the password
            response = supabase.auth.update_user({"password": new_password})

            flash("Password changed successfully!", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(
                "Error changing password. Check your credentials and try again.",
                "danger",
            )
            # print(e)

    return render_template("change_password.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part"
        file = request.files["file"]
        if file.filename == "":
            return "No selected file"
        if file:
            filename = file.filename
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            return redirect(url_for("uploaded_file", filename=filename))
    return """
    <!doctype html>
    <title>Upload Profile Photo</title>
    <h1>Upload new Profile Photo</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    """


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if not is_user_logged_in():
        return redirect(url_for("login"))

    email = session.get("user")  # Logged-in user's email
    user_data = (
        supabase.table("profiles").select("*").eq("email", email).single().execute()
    )
    user_info = user_data.data if user_data.data else {}

    if request.method == "POST":
        updates = {}

        # Handle username update
        new_username = request.form.get("username", "").strip()
        if new_username:
            username_check = (
                supabase.table("profiles")
                .select("email")
                .eq("username", new_username)
                .execute()
            )
            if username_check.data and username_check.data[0]["email"] != email:
                flash(
                    "Username is already taken. Please choose a different one.", "error"
                )
                msg = "Username is already taken. Please choose a different one."
                return render_template("profile.html", user=user_info, usnm_msg=msg)
            updates["username"] = new_username

        # Handle profile photo update
        if "profile_photo" in request.files and request.files["profile_photo"].filename:
            profile_photo = request.files["profile_photo"]

            # Get username for photo filename (use current or new username)
            username = new_username if new_username else user_info.get("username")
            if not username:
                flash(
                    "Error: Username not found. Cannot upload profile photo.", "error"
                )
                return redirect(url_for("profile"))

            photo_filename = f"static/profile_photos/profile_{username}.webp"

            # Convert and save the image
            try:
                from PIL import Image

                img = Image.open(profile_photo)
                img.save(photo_filename, format="WEBP", quality=80)
                updates["profile_photo"] = photo_filename
            except Exception as e:
                flash(f"Error processing image: {str(e)}", "error")
                return redirect(url_for("profile"))

        # Update the database if there are any changes
        if updates:
            supabase.table("profiles").update(updates).eq("email", email).execute()
            flash("Profile updated successfully!", "success")

        return redirect(url_for("profile"))

    return render_template("profile.html", user=user_info)
