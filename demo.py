import os
from itsdangerous import (
    TimedJSONWebSignatureSerializer as Serializer,
    BadSignature, SignatureExpired)
from flask import Flask, jsonify, request
from flask_api import status
from flask_sqlalchemy import SQLAlchemy
from flask_httpauth import HTTPTokenAuth


basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, '../data.sqlite')

app = Flask(__name__)
db = SQLAlchemy(app)
auth = HTTPTokenAuth(scheme='Token')

from models import *
# auth = HTTPBasicAuth()
# creating a blueprint for all routes authenticated by python
# api = Blueprint('api', __name__)
app.config['SECRET_KEY'] = os.environ['SECRET_KEY']
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

current_user = {
    'user_id': None
}


@auth.verify_token
def verify_auth_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        data = s.loads(token)
    except SignatureExpired:
        # The token is valid but has expired
        return None
    except BadSignature:
        # The token is invalid
        return None
    user_id = data['user_id']
    current_user['user_id'] = user_id
    return user_id


@app.errorhandler(404)
def invalid_url(error):
    return jsonify({'message': 'You entered an invalid URL'}), 404


@app.errorhandler(401)
def token_expired_or_invalid(error):
    return jsonify({'message': 'Token Expired/Invalid'}), 401


def verify_password(username, password):
    user = User.query.filter_by(username=username).first()
    if not user or not user.verify_password(password):
        return False
    return user


@app.route('/auth/register', methods=['POST'])
def register_new_user():
    username = request.json.get('username', '')
    password = request.json.get('password', '')

    # check if username or password are provided
    if not username.strip() or not password.strip():
        return jsonify({'message': 'Username/Password Not Provided!'}), 400

    # Check if the username already exists
    user = db.session.query(User).filter_by(username=username).first()
    if user is not None:
        return jsonify({'message': 'User already exists!'}), 400

    user = User(username=username)
    user.set_password(password)
    db.session.add(user)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'error occured while adding user'}), 400
    return jsonify({
        'user': user.username,
        'message': 'login endpoint: localhost:5000/auth/login'
    }), 201


@app.route('/auth/login', methods=['POST'])
def login_user():
    username = request.json.get('username', '')
    password = request.json.get('password', '')

    # check if username or password are provided
    if not username.strip() or not password.strip():
        return jsonify({'message': 'Username/Password Not Provided!'}), 400

    user = verify_password(username, password)
    if user:
        token = user.generate_auth_token()
        return jsonify({
            'message': 'Hello, {0}'.format(user.username),
            'token': 'Token ' + token.decode('ascii')
        }), 201
    else:
        return jsonify({'message': 'invalid username/password'}), 400


@app.route('/bucketlists', methods=['POST'])
@auth.login_required
def create_bucketlist():
    user_id = current_user['user_id']
    name = request.json.get('name', '')

    if not name.strip():
        return jsonify({'message': 'bucketlist name not provided'})

    bucket_found = BucketList.query.filter_by(name=name,
                                              created_by=user_id).first()
    if bucket_found:
        return jsonify({'message': 'bucketlist already exists'}), 400

    bucketlist = BucketList(name=name, created_by=user_id)
    db.session.add(bucketlist)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'message':
                        'error occured while creating bucketlist'}), 400
    return jsonify(bucketlist.get()), 201


@app.route('/bucketlists', methods=['GET'])
@auth.login_required
def get_bucket_lists():
    user_id = current_user['user_id']
    limit = 20
    try:
        page = int(request.args.get('page', 1))
    except Exception:
        return jsonify({'message': 'Invalid Page Value'}), 400
    try:
        limit = int(request.args.get('limit', 20))
    except Exception:
        return jsonify({'message': 'Invalid Limit Value'}), 400
    search = request.args.get('q', '')
    if db.session.query(BucketList).filter_by(created_by=user_id).count() == 0:
        return jsonify({'message': 'no bucketlist found'}), 400

    bucketlist_rows = BucketList.query.filter(
        BucketList.created_by == user_id,
        BucketList.name.like('%' + search + '%')).paginate(page, limit, False)

    all_pages = bucketlist_rows.pages
    next_page = bucketlist_rows.has_next
    previous_page = bucketlist_rows.has_prev

    if next_page:
        next_page_url = (str(request.url_root) + 'bucketlists?' +
                         'limit=' + str(limit) + '&page=' + str(page + 1))
    else:
        next_page_url = None

    if previous_page:
        previous_page_url = (str(request.url_root) + 'bucketlists?' +
                             'limit=' + str(limit) + '&page=' + str(page - 1))

    else:
        previous_page_url = None

    bucketlists = []
    for bucket in bucketlist_rows.items:
        bucketlists.append(bucket.get())
        print(bucket.get())
        paginated_bucketlist = {'total_pages': all_pages,
                                'next_page': next_page_url,
                                'previous_page': previous_page_url,
                                'BucketList': bucketlists
                                }
    return jsonify(paginated_bucketlist), 200


@app.route('/bucketlists/<int:bucketlist_id>', methods=['GET'])
@auth.login_required
def get_specific_bucket_list(bucketlist_id):
    user_id = current_user['user_id']

    bucketlist = db.session.query(BucketList).filter_by(
        bucketlist_id=bucketlist_id,
        created_by=user_id).first()
    if not bucketlist:
        return jsonify({'message': 'bucket list not found'}), 400
    return jsonify(bucketlist.get()), 200


@app.route('/bucketlists/<int:bucketlist_id>', methods=['PUT'])
@auth.login_required
def update_bucket_list(bucketlist_id):
    user_id = current_user['user_id']
    name = request.json.get('name', '')

    if not name.strip():
        return jsonify({'message': 'please provide a name'}), 400

    bucketlist = db.session.query(BucketList).filter_by(
        bucketlist_id=bucketlist_id, created_by=user_id).first()
    if not bucketlist:
        return jsonify({'message': 'bucketlist does not exist'}), 400

    bucketlist.name = name
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'error updating bucketlist'}), 400
    return jsonify(bucketlist.get()), 200


@app.route('/bucketlists/<int:bucketlist_id>', methods=['DELETE'])
@auth.login_required
def delete_bucket_list(bucketlist_id):
    user_id = current_user['user_id']

    delete_bucketlist = db.session.query(BucketList).filter_by(
        bucketlist_id=bucketlist_id, created_by=user_id).first()

    if not delete_bucketlist:
        return jsonify({'message': 'bucketlist not found'})

    try:
        db.session.delete(delete_bucketlist)
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'error deleting bucketlist'}), 400

    return jsonify({}), 204


@app.route('/bucketlists/<int:bucketlist_id>/items', methods=['POST'])
@auth.login_required
def add_bucket_list_item(bucketlist_id):
    user_id = current_user['user_id']
    name = request.json.get('name', '')
    done = request.json.get('done', False)

    if not name.strip():
        return jsonify({'message': 'please provide the name field'})

    if not db.session.query(BucketList).filter_by(
            bucketlist_id=bucketlist_id, created_by=user_id):
        return jsonify({'message': 'bucketlist not found'})

    if db.session.query(BucketListItems).filter_by(bucketlist_id=bucketlist_id,
                                                   name=name).first():
        return jsonify({'message': 'bucketlist item already exists'})

    bucketlistitem = BucketListItems(bucketlist_id=bucketlist_id,
                                     name=name, done=done)

    db.session.add(bucketlistitem)
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify('error adding bucketlist item'), 400
    return jsonify(bucketlistitem.get()), 200


@app.route('/bucketlists/<int:bucketlist_id>/items/<int:item_id>', methods=['PUT'])
@auth.login_required
def update_bucket_list_item(bucketlist_id, item_id):
    user_id = current_user['user_id']
    done = request.json.get('done', False)

    # check if the current user owns this bucket list
    if not db.session.query(BucketList).filter_by(
            bucketlist_id=bucketlist_id, created_by=user_id):
        return jsonify({'message': 'bucketlist not found'}), 400

    # check if the bucket list item exists
    if not db.session.query(BucketListItems).filter_by(item_id=item_id):
        return jsonify({'message': 'bucket list item not found'}), 400

    bucketlistitem = db.session.query(BucketListItems).filter_by(
        item_id=item_id).first()
    if not bucketlistitem:
        return jsonify({'message': 'bucket list item not found'}), 400
    name = request.json.get('name', bucketlistitem.name)
    if not name.strip():
        return jsonify({'message': 'please enter a valid name'}), 400
    bucketlistitem.name = name
    bucketlistitem.done = done

    try:
        db.session.commit()

    except Exception:
        db.session.rollback()
        return jsonify({'message': 'error updating bucket list item'}), 400
    return jsonify(bucketlistitem.get())


@app.route('/bucketlists/<int:bucketlist_id>/items/<int:item_id>', methods=['DELETE'])
@auth.login_required
def delete_bucket_list_item(bucketlist_id, item_id):
    user_id = current_user['user_id']

    if not db.session.query(BucketList).filter_by(
            bucketlist_id=bucketlist_id, created_by=user_id).first():
        return jsonify({'message': 'bucketlist not found'}), 400

    if not db.session.query(BucketListItems).filter_by(item_id=item_id):
        return jsonify({'message': 'bucketlist item does not exist'}), 400

    db.session.query(BucketListItems).filter_by(
        item_id=item_id).delete()
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        return jsonify({'message': 'error deleting bucketlist item'}), 400
    return jsonify({}), 204


if __name__ == '__main__':
    app.run(debug=True)
