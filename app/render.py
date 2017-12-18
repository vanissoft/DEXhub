"""
20170330 Vanissoft


	render templates

"""

import string

def template():
	return response_html(open(pfil).read())

class Render():
	"""
	t = Render('index.html').render()
	Sustituye marcadores ${var} por su valor o por el fichero que referencia
	${v1}    ${header.html}
	"""

	def __init__(self, fname):
		self.filename = fname.split('/')[-1]
		self.path = '/'.join([x for x in fname.split('/')[:-1]]) + '/'
		self.template = self.path + self.filename
		self.file_o = open(self.template).read()
		self.output = None
		self.files = None

	async def parse(self):
		self.output = ''
		self.files = []
		fo = self.file_o.split('${')
		if len(fo) < 2:
			return fo[0]
		for i in fo:
			if '}' in i:
				f1 = i.find('}')
				fname = i[:f1]
				self.files.append(fname)
				self.output += open(self.path+fname).read()
				self.output += i[f1+1:]
			else:
				self.output += i
		return self.output

	def froga(self):
		tmp = self.file_o
		print(tmp)

if __name__ == '__main__':
	print("import in main")
