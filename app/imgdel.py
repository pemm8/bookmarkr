import os, shutil
from app import *

dirc = os.getcwd() + '/static/img/'
dird = os.getcwd() + '/static/img/del/'

ents = []
for b in Bookmark.query.all():
	nametoappend = b.image.replace('/static/img/','')
	ents.append(nametoappend)

files = []
for filenames in os.walk(dirc):
	for filename in filenames:
		files.append(filename)
files = files[2]

if len(files) > len(ents):
	n = len(files) - len(ents)

	for file in files:
		if not file in ents:
			shutil.move(dirc + file, dird + file)