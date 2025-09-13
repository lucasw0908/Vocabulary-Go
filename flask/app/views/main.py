import logging
import json
import os
import random

from flask import Blueprint, Response, abort, render_template, redirect, make_response, url_for, flash, request, session, g
from flask_babel import _, refresh

from ..config import (
    BASEDIR, DATETIME_FORMAT, DEFAULT_ITEMS_PER_PAGE,
    GITHUB_LINK, DISCORD_LINK, TWITTER_LINK, FACEBOOK_LINK, INSTAGRAM_LINK,
    SUPPORTED_LANGUAGES, DEFAULT_LOCALE,
    FALLBACK_QUOTES
)
from ..models import db, Libraries, Sentences, Users, Words
from ..utils.forms import LibraryForm
from ..utils.login_manager import current_user
from ..utils.checker import word_checker


log = logging.getLogger(__name__)
main = Blueprint("main", __name__)

main.add_url_rule("/github", "github", lambda: redirect(GITHUB_LINK))
main.add_url_rule("/discord", "discord", lambda: redirect(DISCORD_LINK))
main.add_url_rule("/twitter", "twitter", lambda: redirect(TWITTER_LINK))
main.add_url_rule("/facebook", "facebook", lambda: redirect(FACEBOOK_LINK))
main.add_url_rule("/instagram", "instagram", lambda: redirect(INSTAGRAM_LINK))


@main.after_request
def checking(response: Response):
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "deny"
    
    return response


@main.before_app_request
def set_g_locale():
    
    refresh()
        
    if "lang" in session and session["lang"] in SUPPORTED_LANGUAGES:
        g.locale = session["lang"]
        
    elif current_user.is_authenticated and getattr(current_user, "locale", None) in SUPPORTED_LANGUAGES:
        g.locale = current_user.locale
        
    else:
        g.locale = DEFAULT_LOCALE
    

@main.route("/set_language/<lang_code>")
def set_language(lang_code):
    
    if lang_code in SUPPORTED_LANGUAGES:
        session['lang'] = lang_code
        
    return redirect(request.referrer or url_for('main.index'))


@main.route("/", methods=["GET"])
def index():
    stastistics = {}
    stastistics["users"] = len(Users.query.all())
    stastistics["words"] = len(Words.query.all())
    stastistics["libraries"] = len(Libraries.query.all())
    return render_template("index.html", current_user=current_user, statistics=stastistics)


@main.route("/word_test", methods=["GET"])
def word_test():
    
    if Libraries.query.filter_by(name=current_user.current_library).first() is None:
        flash(_("Please choose a library first."), "warning")
        return redirect(url_for("main.library"))
    
    words = []

    for word in Words.query.join(Libraries).filter(Libraries.name == current_user.current_library).all():
        word: Words
        words.append({
            "Chinese": word.chinese,
            "English": word.english
        })
        
    if len(words) == 0:
        flash(_("No words found in the current library."), "warning")
        return render_template("word_test.html", current_user=current_user)
    
    random.shuffle(words)

    return render_template("word_test.html", current_user=current_user, words=words)


@main.route("/sentence_test", methods=["GET"])
def sentence_test():
    
    if Libraries.query.filter_by(name=current_user.current_library).first() is None:
        flash(_("Please choose a library first."), "warning")
        return redirect(url_for("main.library"))
    
    skipping = 0
    questions = []
    words: list[Words] = Words.query.join(Libraries).filter(Libraries.name == current_user.current_library).all()
    
    for w in words:
        sentences = Sentences.query.filter_by(word_english=w.english).all()
        
        if len(sentences) == 0:
            questions.append({
                "chinese": None,
                "english": None,
                "word_chinese": None,
                "word_english": None,
            })
            skipping += 1
            log.debug(f"No sentences found for word '{w.english}' in library '{current_user.current_library}'.")
            continue
        
        s: Sentences = random.choice(sentences)
        
        questions.append({
            "chinese": s.chinese,
            "english": s.english,
            "word_chinese": s.word_chinese,
            "word_english": s.word_english,
        })  
        
    if len(questions) == skipping:
        log.warning(f"No sentences found in the current library '{current_user.current_library}'.")
        flash(_("No sentences found in the current library."), "warning")
        return render_template("sentence_test.html", current_user=current_user)
    
    return render_template("sentence_test.html", current_user=current_user, questions=questions)


@main.route("/library", methods=["GET"])
def library():
    
    if current_user.is_authenticated and current_user.is_admin:
        library_models: list[Libraries] = Libraries.query.all()
        
    elif current_user.is_authenticated:
        library_models: list[Libraries] = Libraries.query.filter(
            Libraries.public | (Libraries.author_id == current_user.id)
        ).all()
        
    else:
        library_models: list[Libraries] = Libraries.query.filter_by(public=True).all()
    
    libraries: list[dict] = [{
        "name": library.name,
        "description": library.description,
        "author": library.user.username,
        "created_at": library.created_at.strftime(DATETIME_FORMAT),
        "updated_at": library.updated_at.strftime(DATETIME_FORMAT),
        "count": len(library.words),
        "favorite_count": len(library.favorite_users),
        "is_favorited": (current_user in library.favorite_users) if current_user.is_authenticated else False,
        "is_public": library.public,
        "is_owner": (library.author_id == current_user.id) if current_user.is_authenticated else False
    } for library in library_models]
    
    user_info = {
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
        "library": current_user.current_library,
        "avatar_url": current_user.avatar_url,
        "locale": current_user.locale,
        "link_discord": current_user.discord_id is not None,
        "link_google": current_user.google_id is not None,
    }
    
    quote: list[str] = FALLBACK_QUOTES
    
    libraries.sort(key=lambda x: (-x["is_favorited"], -x["favorite_count"]))
    random.shuffle(quote)

    return render_template(
        "library.html",
        current_user=current_user,
        libraries=libraries,
        user_info=user_info,
        quote=quote,
        items_per_page=DEFAULT_ITEMS_PER_PAGE
    )


@main.route("/library/edit", methods=["GET"])
def select_library_to_edit():
    if not current_user.is_authenticated:
        flash(_("You must be logged in to edit a library."), "error")
        return redirect(url_for("main.library"))

    # Fetch only libraries owned by the current user
    owned: list[Libraries] = Libraries.query.filter_by(author_id=current_user.id).all()
    libraries = [{
        "name": lib.name,
        "description": lib.description,
        "count": len(lib.words),
        "public": lib.public,
    } for lib in owned]

    return render_template(
        "library_edit_select.html",
        current_user=current_user,
        libraries=libraries,
    )


@main.route("/library/create", methods=["GET", "POST"])
def create_library():

    form = LibraryForm()
    
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            log.error("User must be logged in to create a library.")
            flash(_("You must be logged in to create a library."), "error")
            return redirect(url_for("main.library"))
        if not current_user.email_verified:
            log.warning(f"Unverified user '{current_user.username}' attempted to create a library.")
            flash(_("Please verify your email before creating a library."), "warning")
            return redirect(url_for("main.library"))
        words_data = form.words.data.strip()
        
        # Check if user has reached the library limit (5 libraries max for regular users)
        if not current_user.is_admin and not current_user.unlimited_access:
            user_library_count = Libraries.query.filter_by(author_id=current_user.id).count()
            if user_library_count >= 5:
                log.warning(f"User '{current_user.username}' has reached the library limit (5).")
                flash(_("You have reached the maximum number of libraries (5). Please upgrade for unlimited access."), "error")
                return redirect(url_for("main.library"))
        
        if form.name.data.strip() == "":
            log.error("Library name cannot be empty.")
            flash(_("Library name cannot be empty."), "error")
            return redirect(url_for("main.library"))
        
        elif Libraries.query.filter_by(name=form.name.data.strip()).first() is not None:
            log.error(f"Library '{form.name.data.strip()}' already exists.")
            flash(_("Library '%(name)s' already exists.", name=form.name.data.strip()), "error")
            return redirect(url_for("main.library"))
    
        try:
            words_json = json.loads(words_data)
            word_checker(words_json)
            
            # Check if library exceeds word limit (500 words max for regular users)
            if not current_user.is_admin and not current_user.unlimited_access:
                if len(words_json) > 500:
                    log.warning(f"User '{current_user.username}' attempted to create a library with {len(words_json)} words (limit is 500).")
                    flash(_("Library exceeds maximum word limit (500). Please upgrade for unlimited access."), "error")
                    return redirect(url_for("main.library"))
            
        except json.JSONDecodeError:
            log.error("Invalid JSON format for words.")
            flash(_("Invalid JSON format for words."), "error")
            return redirect(url_for("main.library"))
        
        except Exception as e:
            log.error(f"Error validating words: {e}")
            flash(_("Invalid words format. Please check your input."), "error")
            return redirect(url_for("main.library"))
        
        library = Libraries(
            name=form.name.data,
            description=form.description.data.strip() if form.description.data else "",
            public=form.public.data,
            author_id=current_user.id
        )
        db.session.add(library)
        db.session.commit()
        
        for word in words_json:
            if "Chinese" not in word or "English" not in word:
                log.error("Missing 'Chinese' or 'English' key in words JSON.")
                flash(_("Each word must have 'Chinese' and 'English' keys."), "error")
                return redirect(url_for("main.library"))
            
            word_instance = Words(
                chinese=word["Chinese"],
                english=word["English"]
            )
            # Associate the word with the created library
            word_instance.library = library
            db.session.add(word_instance)
        
        current_user.current_library = library.name
        db.session.commit()
        log.info(f"Library '{library.name}' created by user '{current_user.username}'.")

        return redirect(url_for("main.library"))
    
    else:
        if form.errors:
            log.error(f"Form validation errors: {form.errors}")
            flash(_("Form validation failed. Please check your input."), "error")
            return redirect(url_for("main.library"))
        
        if not current_user.is_authenticated:
            log.error("User must be logged in to create a library.")
            flash(_("You must be logged in to create a library."), "error")
            return redirect(url_for("main.library"))
        
        return render_template(
            "library_create.html",
            current_user=current_user,
            form=form,
        )
        

@main.route("/library/edit/<string:library_name>", methods=["GET", "POST"])
def edit_library(library_name: str):
    form = LibraryForm()
    library: Libraries = Libraries.query.filter_by(name=library_name).first()
    
    if library is None:
        log.warning(f"Library '{library_name}' not found.")
        abort(404)
        
    if not current_user.is_authenticated:
        flash(_("You must be logged in to edit a library."), "error")
        return redirect(url_for("main.library"))
    if not current_user.email_verified:
        log.warning(f"Unverified user '{current_user.username}' attempted to edit library '{library_name}'.")
        flash(_("Please verify your email before editing a library."), "warning")
        return redirect(url_for("main.library"))
    if library.author_id != current_user.id and not current_user.is_admin:
        log.warning(f"User '{current_user.username}' does not have permission to edit library '{library_name}'.")
        abort(403)
    
    if request.method == "POST" and form.validate_on_submit():
        words_data = form.words.data.strip()
        form_name = form.name.data.strip()
        
        if not form_name:
            flash(_("Library name cannot be empty."), "error")
            return redirect(url_for("main.library"))
        
        elif form_name != library.name and Libraries.query.filter_by(name=form_name).first() is not None:
            flash(_("Library '%(name)s' already exists.", name=form_name), "error")
            return redirect(url_for("main.library"))
    
        try:
            words_json = json.loads(words_data)
            word_checker(words_json)
            
            # Check if library exceeds word limit (500 words max for regular users)
            if not current_user.is_admin and not current_user.unlimited_access:
                if len(words_json) > 500:
                    log.warning(f"User '{current_user.username}' attempted to update library with {len(words_json)} words (limit is 500).")
                    flash(_("Library exceeds maximum word limit (500). Please upgrade for unlimited access."), "error")
                    return redirect(url_for("main.library"))
            
        except json.JSONDecodeError:
            log.error("Invalid JSON format for words.")
            flash(_("Invalid JSON format for words."), "error")
            return redirect(url_for("main.library"))
        
        except Exception as e:
            log.error(f"Error validating words: {e}")
            flash(_("Invalid words format. Please check your input."), "error")
            return redirect(url_for("main.library"))
        
        library.name = form.name.data
        library.description = form.description.data.strip() if form.description.data else ""
        library.public = form.public.data
        
        Words.query.filter_by(_library_id=library.id).delete()
        
        for word in words_json:
            if "Chinese" not in word or "English" not in word:
                flash(_("Missing 'Chinese' or 'English' key in words JSON."), "error")
                return redirect(url_for("main.library"))
            
            word_instance = Words(
                chinese=word["Chinese"],
                english=word["English"]
            )
            word_instance.library = library
            db.session.add(word_instance)
        
        db.session.commit()
        log.info(f"Library '{library.name}' updated by user '{current_user.username}'.")
        
    form.name.data = library.name
    form.name.render_kw = {"readonly": True}
    form.description.data = library.description
    form.public.data = library.public
    
    form.words.data = json.dumps([{"Chinese": word.chinese, "English": word.english} for word in library.words], ensure_ascii=False, indent=4)
    return render_template("library_edit.html", current_user=current_user, form=form) 


@main.route("/card", methods=["GET"])
def card():
    
    if Libraries.query.filter_by(name=current_user.current_library).first() is None:
        flash(_("Please choose a library first."), "warning")
        return redirect(url_for("main.library"))
    
    words = []

    for word in Words.query.join(Libraries).filter(Libraries.name == current_user.current_library).all():
        word: Words
        words.append({
            "Chinese": word.chinese,
            "English": word.english
        })
        
    if len(words) == 0:
        flash(_("No words found in the current library."), "warning")
        return render_template("card.html", current_user=current_user)
    
    random.shuffle(words)

    return render_template("card.html", current_user=current_user, words=words)


@main.route("/tos", methods=["GET"])
def tos_pdf():
    response = make_response(open(os.path.join(BASEDIR, "static", "assets", "tos.pdf"), "rb").read())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "inline; filename=tos.pdf"
    return response
