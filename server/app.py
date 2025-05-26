#!/usr/bin/env python3

from flask import Flask, make_response, jsonify, request, session
from flask_migrate import Migrate
from flask_restful import Api, Resource

from models import db, Article, User, ArticlesSchema, UserSchema

app = Flask(__name__)
app.secret_key = b'Y\xf1Xz\x00\xad|eQ\x80t \xca\x1a\x10K'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.json.compact = False

migrate = Migrate(app, db)

db.init_app(app)

api = Api(app)

class ClearSession(Resource):

    def delete(self):
        session['page_views'] = None
        session['user_id'] = None
        return {}, 204

class IndexArticle(Resource):
    
    def get(self):
        articles = [ArticlesSchema().dump(article) for article in Article.query.all()]
        return articles, 200

class ShowArticle(Resource):

    def get(self, id):
        session['page_views'] = 0 if not session.get('page_views') else session.get('page_views')
        session['page_views'] += 1

        if session['page_views'] <= 3:
            article = Article.query.filter(Article.id == id).first()
            article_json = ArticlesSchema().dump(article)
            return make_response(article_json, 200)

        return {'message': 'Maximum pageview limit reached'}, 401

# Authentication Resource Classes

class Login(Resource):
    
    def post(self):
        """
        Handle user login by username and create session.
        
        Expects JSON: {"username": "some_username"}
        Sets session['user_id'] and returns user data
        """
        # Step 1: Get username from request JSON
        data = request.get_json()
        username = data.get('username')
        
        # Step 2: Find user in database by username
        user = User.query.filter(User.username == username).first()
        
        # Step 3: Set session and return user data
        if user:
            session['user_id'] = user.id
            return UserSchema().dump(user), 200
        else:
            # Optional: Handle invalid users (not required by tests)
            return {'message': 'Invalid login'}, 401

class Logout(Resource):
    
    def delete(self):
        """
        Log out user by removing user_id from session.
        
        Returns: 204 No Content status code with no data
        """
        # Remove the user_id value from session
        session['user_id'] = None
        
        # Return 204 No Content with no data
        return {}, 204

class CheckSession(Resource):
    
    def get(self):
        """
        Check if user is logged in by verifying session.
        
        Returns: User data if logged in (200), empty dict if not (401)
        """
        # Get user_id value from session (may not exist)
        user_id = session.get('user_id')
        
        if user_id:
            # Session has user_id - look up user and return data
            user = User.query.filter(User.id == user_id).first()
            if user:
                return UserSchema().dump(user), 200
        
        # Session does not have user_id - return 401 with empty dict
        return {}, 401

# Add existing routes to API
api.add_resource(ClearSession, '/clear')
api.add_resource(IndexArticle, '/articles')
api.add_resource(ShowArticle, '/articles/<int:id>')

# Add authentication routes to API
api.add_resource(Login, '/login')
api.add_resource(Logout, '/logout')
api.add_resource(CheckSession, '/check_session')

if __name__ == '__main__':
    app.run(port=5555, debug=True)