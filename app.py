import os

from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import db_session
from models import Image

import boto3
from boto.s3.key import Key
from boto3.s3.transfer import S3Transfer
import botocore

AWS_BUCKET_ID = os.environ['AWS_BUCKET_ID']
AWS_BUCKET_URL = os.environ['AWS_BUCKET_URL']
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

app = Flask(__name__)

def get_aws_bucket():
	client = boto3.client(
		's3', 
		aws_access_key_id=AWS_ACCESS_KEY_ID, 
		aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
	return S3Transfer(client)

def upload_to_s3(filename, content, mimetype):
	transfer = get_aws_bucket()
	transfer.upload_file(
		content,
		AWS_BUCKET_ID, 
		filename,
		extra_args={'Metadata': {'Content-Type': mimetype},
					'ACL': 'public-read'}
	)
	# key.set_acl('public-read')

def delete_from_s3(filename):
	key = get_aws_bucket()
	key.key = filename
	key.delete()

@app.route('/', methods=['GET', 'POST'])
def index():
	get_aws_bucket()
	if request.method == 'POST':

		title = request.form.get('title', '')
		image = request.files['image']
		filename = image.filename
		mimetype = image.mimetype

		try:
			upload_to_s3(filename, image, mimetype)
			image = Image(
				title=title,
				filename=filename,
				url=os.path.join(AWS_BUCKET_URL, filename)
			)
			db_session.add(image)
			db_session.commit()
		except Exception as e:
			print e

		return redirect(url_for('index'))

	images = Image.query.all()
	return render_template('index.html', images=images)

@app.route('/delete', methods=['POST'])
def delete():
	filename = request.data
	image = Image.query.filter_by(filename=filename).first()
	message = 'Image deleted'

	try:
		delete_from_s3(filename)
		db_session.delete(image)
		db_session.commit()
	except Exception as e:
		message = 'Error deleting message'
		print e

	return jsonify(message=message)


if __name__ == '__main__':
    app.run(debug=True)