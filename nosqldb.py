# -*- coding: utf-8 -*-

from blitzdb import Document, FileBackend


class Author(Document):
	pass
	# class Meta(Document.Meta):
	# 	primary_key = 'first_name'


def main():
	backend = FileBackend("./my-db", {'serializer_class': 'json'})
	backend.autocommit = True
	backend.create_index(Author, 'first_name', ephemeral=False)

	query_insert = {
		'first_name' : 'Charlie',
		'last_name'  : 'Chaplin',
		'is_funny'   : True,
		'birth_year' : 1889,
		'filmography': [
			{
				'holaaa': "mundo"
			}
		]
	}

	query = {
		'first_name' : 'Charlie',
		'last_name'  : 'Chaplin',
		'is_funny'   : True,
		'birth_year' : 1889,
		'filmography': {"holaaa": "mundo"}
	}

	charlie_chaplin = Author(query_insert, default_backend=backend)

	# backend.get_collection_for_cls(charlie_chaplin)

	try:
		backend.get(Author, query)
		print("found, not saving")

	except Author.DoesNotExist:
		# no 'Charlie' in the database
		print("not found, saving")
		charlie_chaplin.save()

	# charlie_chaplin.save(backend)
	# backend.commit()

	return
	try:
		actor = backend.get(Author, {'first_name': 'Charlie'})

		print(actor)
	except Author.DoesNotExist:
		# no 'Charlie' in the database
		pass
	except Author.MultipleDocumentsReturned as e:
		print(e)


if __name__ == '__main__':
	main()
