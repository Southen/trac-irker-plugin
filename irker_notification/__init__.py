import json
import socket
import re
from trac.core import *
from trac.config import Option, IntOption
from trac.ticket.api import ITicketChangeListener
#from trac.versioncontrol.api import IRepositoryChangeListener
#from trac.wiki.api import IWikiChangeListener

def prepare_ticket_values(ticket, action=None):
	values = ticket.values.copy()
	values['id'] = "#" + str(ticket.id)
	values['action'] = action
	values['url'] = ticket.env.abs_href.ticket(ticket.id)
	values['project'] = ticket.env.project_name.encode('utf-8').strip()
	return values

class IrkerNotifcationPlugin(Component):
	implements(ITicketChangeListener)
	host = Option('irker', 'host', 'localhost',
		doc="Host on which the irker daemon resides.")
	port = IntOption('irker', 'port', 6659,
		doc="Irker listen port.")
	target = Option('irker', 'target', 'irc://localhost/#commits',
		doc="IRC channel URL to which notifications are to be sent.")

	def notify(self, type, values):
		values['type'] = type
		values['author'] = re.sub(r' <.*', '', values['author'])
		#template = '%(project)s/%(branch)s %(rev)s %(author)s: %(logmsg)s'
		#template = '%(project)s %(rev)s %(author)s: %(logmsg)s'
		template = '%(project)s %(type)s %(id)s %(action)s %(author)s: %(summary)s'
		message = template % values
		#message = ' '.join(['%s=%s' % (key, value) for (key, value) in values.items()])
		data = {"to": self.target, "privmsg": message.encode('utf-8').strip() }
		try:
			s = socket.create_connection((self.host, self.port))
			s.sendall(json.dumps(data))
		except socket.error:
			return False
		return True

	def ticket_created(self, ticket):
		values = prepare_ticket_values(ticket, 'created')
		values['author'] = values['reporter']
		self.notify('ticket', values)

	def ticket_changed(self, ticket, comment, author, old_values):
		action = 'changed'
		if 'status' in old_values:
			if 'status' in ticket.values:
				if ticket.values['status'] != old_values['status']:
					action = ticket.values['status']
		values = prepare_ticket_values(ticket, action)
		values.update({
			'comment':	comment or '',
			'author':	author or '',
			'old_values':	old_values
		})
		self.notify('ticket', values)

	def ticket_deleted(self, ticket):
		pass

	#def wiki_page_added(self, page):
	#def wiki_page_changed(self, page, version, t, comment, author, ipnr):
	#def wiki_page_deleted(self, page):
	#def wiki_page_version_deleted(self, page):
