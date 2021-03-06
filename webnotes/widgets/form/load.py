# Copyright (c) 2012 Web Notes Technologies Pvt Ltd (http://erpnext.com)
# 
# MIT License (MIT)
# 
# Permission is hereby granted, free of charge, to any person obtaining a 
# copy of this software and associated documentation files (the "Software"), 
# to deal in the Software without restriction, including without limitation 
# the rights to use, copy, modify, merge, publish, distribute, sublicense, 
# and/or sell copies of the Software, and to permit persons to whom the 
# Software is furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in 
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, 
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A 
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT 
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF 
# CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE 
# OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 

from __future__ import unicode_literals
import webnotes, json
import webnotes.model.doc
import webnotes.utils

@webnotes.whitelist()
def getdoc(doctype, name, user=None):
	"""
	Loads a doclist for a given document. This method is called directly from the client.
	Requries "doctype", "name" as form variables.
	Will also call the "onload" method on the document.
	"""

	import webnotes
	
	if not (doctype and name):
		raise Exception, 'doctype and name required!'
	
	if not name: 
		name = doctype

	if not webnotes.conn.exists(doctype, name):
		return []

	try:
		bean = webnotes.bean(doctype, name)
		bean.run_method("onload")

		doclist = bean.doclist

		# add file list
		set_docinfo(doctype, name)
		
	except Exception, e:
		webnotes.errprint(webnotes.utils.getTraceback())
		webnotes.msgprint('Did not load.')
		raise e

	if bean and not name.startswith('_'):
		webnotes.user.update_recent(doctype, name)
	
	webnotes.response['docs'] = doclist

@webnotes.whitelist()
def getdoctype(doctype, with_parent=False, cached_timestamp=None):
	"""load doctype"""
	import webnotes.model.doctype
	import webnotes.model.meta
	
	doclist = []
	
	# with parent (called from report builder)
	if with_parent:
		parent_dt = webnotes.model.meta.get_parent_dt(doctype)
		if parent_dt:
			doclist = webnotes.model.doctype.get(parent_dt, processed=True)
			webnotes.response['parent_dt'] = parent_dt
	
	if not doclist:
		doclist = webnotes.model.doctype.get(doctype, processed=True)
	
	if cached_timestamp and doclist[0].modified==cached_timestamp:
		return "use_cache"
	
	webnotes.response['docs'] = doclist

def set_docinfo(doctype, name):
	webnotes.response["docinfo"] = {
		"attachments": add_attachments(doctype, name),
		"comments": add_comments(doctype, name),
		"assignments": add_assignments(doctype, name)
	}

def add_attachments(dt, dn):
	attachments = {}
	for f in webnotes.conn.sql("""select name, file_name, file_url from
		`tabFile Data` where attached_to_name=%s and attached_to_doctype=%s""", 
			(dn, dt), as_dict=True):
		attachments[f.file_url or f.file_name] = f.name

	return attachments
		
def add_comments(dt, dn, limit=20):
	cl = webnotes.conn.sql("""select name, comment, comment_by, creation from `tabComment` 
		where comment_doctype=%s and comment_docname=%s 
		order by creation desc limit %s""" % ('%s','%s', limit), (dt, dn), as_dict=1)
		
	return cl
	
def add_assignments(dt, dn):
	cl = webnotes.conn.sql_list("""select owner from `tabToDo`
		where reference_type=%(doctype)s and reference_name=%(name)s
		order by modified desc limit 5""", {
			"doctype": dt,
			"name": dn
		})
		
	return cl

@webnotes.whitelist()
def get_badge_info(doctypes, filters):
	filters = json.loads(filters)
	doctypes = json.loads(doctypes)
	filters["docstatus"] = ["!=", 2]
	out = {}
	for doctype in doctypes:
		out[doctype] = webnotes.conn.get_value(doctype, filters, "count(*)")

	return out