import logging

from flask import abort
from flask_admin import Admin, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask_admin.menu import MenuLink

from ..models import db, Libraries, Sentences, Users, Words
from ..utils.login_manager import current_user
from .secret import hash_password


log = logging.getLogger(__name__)


class SecureAdminIndexView(AdminIndexView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        abort(403)
        

class SecureModelView(ModelView):
    list_template = "admin/list.html"
    create_template = "admin/create.html"
    edit_template = "admin/edit.html"
    details_template = "admin/details.html"
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        abort(403)
        
        
class UsersModelView(SecureModelView):
    SYSTEM_USER_ID = 1
    
    can_create = True
    can_edit = True
    can_delete = True
    
    column_list = [
        "id", "username", "email", "is_admin", "unlimited_access",
        "locale", "current_library",
        "discord_id", "google_id",
        "created_at", "updated_at"
    ]
    column_searchable_list = ["username", "email"]
    column_filters = ["id", "is_admin", "unlimited_access", "locale", "created_at", "updated_at", "libraries", "current_library"]
    
    form_columns = ["username", "email", "password", "is_admin", "unlimited_access", "locale", "bio"]
    
    def on_model_change(self, form, model: Users, is_created):
        if is_created or form.password.data:
            model.password = hash_password(form.password.data)
        return super().on_model_change(form, model, is_created)

    def delete_model(self, model):
        if model.id == self.SYSTEM_USER_ID:
            return False
        return super().delete_model(model)
    
    
class WordsModelView(SecureModelView):
    can_create = True
    can_edit = False
    can_delete = True
    
    column_list = ["id", "chinese", "english", "library", "created_at", "updated_at"]
    column_searchable_list = ["chinese", "english"]
    column_filters = ["id", "created_at", "updated_at", "library"]
    
    form_columns = ["chinese", "english", "library"]
    
    
class LibrariesModelView(SecureModelView):
    can_create = True
    can_edit = True
    can_delete = True
    
    column_list = ["id", "name", "description", "public", "user", "created_at", "updated_at"]
    column_searchable_list = ["name", "description"]
    column_filters = ["id", "created_at", "updated_at", "user"]
    
    form_columns = ["name", "description", "public", "user"]
    
    
class SentencesModelView(SecureModelView):
    can_create = True
    can_edit = True
    can_delete = True
    
    column_list = ["id", "chinese", "english", "word_chinese", "word_english", "created_at", "updated_at"]
    column_searchable_list = ["chinese", "english", "word_chinese", "word_english"]
    column_filters = ["id", "created_at", "updated_at"]
    
    form_columns = ["chinese", "english", "word_chinese", "word_english"]
        

def init_admin(app):
    """
    Initialize the Flask-Admin interface.
    
    Parameters
    ----------
    app: :class:`Flask`
        The flask app.
    """
    
    admin = Admin(
        app,
        name="Vocabulary Admin",
        template_mode="bootstrap3",
        base_template="admin/base_view.html",
        index_view=SecureAdminIndexView(
            name="Home", 
            template="admin/index.html",
            url="/admin"
        )
    )
    admin.add_view(UsersModelView(Users, db.session, name="Users"))
    admin.add_view(WordsModelView(Words, db.session, name="Words"))
    admin.add_view(LibrariesModelView(Libraries, db.session, name="Libraries"))
    admin.add_view(SentencesModelView(Sentences, db.session, name="Sentences"))
    admin.add_link(MenuLink(name="Back to Site", url="/"))

    return admin
