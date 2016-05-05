import os
import mimetypes
import cStringIO
from PIL import Image as PIL_Image

from flask import Flask, render_template, request, redirect, url_for, jsonify
from database import db_session
from models import Image

import boto3

AWS_BUCKET_ID = os.environ['AWS_BUCKET_ID']
AWS_BUCKET_URL = os.environ['AWS_BUCKET_URL']
AWS_ACCESS_KEY_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_SECRET_ACCESS_KEY = os.environ['AWS_SECRET_ACCESS_KEY']

app = Flask(__name__)

def get_s3_obj():
	client = boto3.client(
		's3', 
		aws_access_key_id=AWS_ACCESS_KEY_ID, 
		aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
	s3 = boto3.resource('s3')
	return s3

def upload_to_s3(filename, content, mimetype):
	s3 = get_s3_obj()
	obj = s3.Object(AWS_BUCKET_ID, filename)
	response = obj.put(
		ACL='public-read',
		Body=content,
		ContentType=mimetype
		)
	print response
	return response

def delete_from_s3(filename):
	s3 = get_s3_obj()
	bucket = s3.Bucket(AWS_BUCKET_ID)
	response = bucket.delete_objects(
		Delete={
			'Objects': [
				{
					'Key': filename,
				}
			]
		}
	)

def thumbnail(file):
	size = 75, 75
	im = PIL_Image.open(file)
	filename, ext = file.filename.split('.')
	filename = filename + '-thumb.' + ext
	im.thumbnail(size)
	memory_file = cStringIO.StringIO()
	im.save(memory_file, ext)
	return memory_file, filename

@app.route('/', methods=['GET', 'POST'])
def index():
	if request.method == 'POST':

		title = request.form.get('title', '')
		image = request.files['image']
		filename = image.filename
		mimetype = image.mimetype

		try:
			upload_to_s3(filename, image, mimetype)
			thumbnail_file, thumbnail_filename = thumbnail(image)
			upload_to_s3(thumbnail_filename, thumbnail_file.getvalue(), mimetype)
			thumbnail_file.close()

			image = Image(
				title=title,
				filename=filename,
				url=os.path.join(AWS_BUCKET_URL, filename),
				thumb_url=os.path.join(AWS_BUCKET_URL, thumbnail_filename),
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