#
#
# (c) 2018 elias/vanissoft
#
#
#
"""
"""




from config import *
import json
from cryptography.fernet import Fernet
import hashlib
import base64





def check_for_master_password():
	msg = None
	if not master_unlocked():
		msg = "Unlock with master password first."
	elif master_hash() is None:
		msg = "Setup a master password first and then unlock."
	if msg is not None:
		Redisdb.rpush("datafeed", json.dumps({'module': "general", 'message': msg,'error': True}))
		return False
	return True


def master_hash(hash=None):
	if hash is None:
		rtn = Redisdb.get("master_hash")
		if rtn is None:
			rtn = Redisdb.get("settings_misc")
			if rtn is None:
				return None
			settings = json.loads(rtn.decode('utf8'))
			if "master_password" in settings:
				hash = settings['master_password']
				Redisdb.set("master_hash", hash)
			else:
				return None
		else:
			hash = rtn.decode('utf8')
	else:
		Redisdb.set("master_hash", hash)
	return hash


def master_unlocked(status=None):
	if status is None:
		rtn = Redisdb.get("master_unlocked")
		if rtn is None:
			return False
		status = (rtn.decode('utf8')=='1')
	else:
		Redisdb.set("master_unlocked", status)
		status = (status == '1')
	return status


def generate_mp(pwtxt, key=False):
	hash1 = base64.urlsafe_b64encode(hashlib.sha256(bytes(str(pwtxt), 'utf8')).digest()).decode('utf8')
	hash2 = base64.urlsafe_b64encode(hashlib.sha256(bytes(str(hash1), 'utf8')).digest()).decode('utf8') + ('unlocked' if key else '')
	cipher = Fernet(hash1)  # cipher with hash
	return cipher.encrypt(hash2.encode('utf8')).decode(), hash1


def store_mp(pwtxt):
	mp = generate_mp(pwtxt, True)
	Redisdb.set('stored_password', mp[0])
	Redisdb.setex('master_hash', 60*60, mp[1])
	print('store_mp master_hash:', mp[1])
	print("store_mp stored_pass:", mp[0])


def check_mp(pwtxt):
	hash = base64.urlsafe_b64encode(hashlib.sha256(bytes(str(pwtxt), 'utf8')).digest()).decode('utf8')
	mh = Redisdb.get('stored_password').decode('utf8')
	print("check_mp hash:", hash)
	print("check_mp stored_pass):", mh)
	cipher = Fernet(hash)  # cipher with hash
	tmp = cipher.decrypt(mh.encode('utf8')).decode('utf8')
	if 'unlocked' in tmp:
		if Redisdb.get('master_hash') is None:
			Redisdb.setex('master_hash', 60 * 60, generate_mp(pwtxt, key=True)[1])
		return True
	return False

def encrypt_data(data):
	mh = Redisdb.get('master_hash')
	if mh is None:
		return None
	cipher = Fernet(mh)  # cipher with hash
	enc = cipher.encrypt(data.encode('utf8')).decode()
	return enc

def decrypt_data(data):
	mh = Redisdb.get('master_hash')
	if mh is None:
		return None
	cipher = Fernet(mh)  # cipher with hash
	dec = cipher.decrypt(data.encode('utf8')).decode('utf8')
	return dec




if __name__ == "__main__":
	print(store_mp('123'))
	print(check_mp('123'))
	enc = encrypt_data('12312213213123')
	print(enc)
	dec = decrypt_data(enc)
	print(dec)
	pass