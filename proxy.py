from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES,PKCS1_v1_5
from pwn import *
import base64

conn1 = remote("127.0.0.1",8888)
conn2 = remote("127.0.0.1",8889)

with open("rsa.private","rb") as keyMITM :
    privateKeyMITM = RSA.importKey(keyMITM.read())
    cipherRSA_MITM = PKCS1_v1_5.new(privateKeyMITM)

with open("rsaPKCS1.public","r") as publicKeyMITM :
    publicKeyMITM = base64.b64encode(publicKeyMITM.read().encode())
    
s = get_random_bytes(128)

with open("result","ab") as resultFile :    
    ogPublicKey1 = conn1.recv(4096)
	
    conn2.sendline(publicKeyMITM)
    ogPublicKey2 = conn2.recv(4096)

    #Since the RSA is only to encrypt the AES key to be able to send safely, we won't need to encrypt/decrypt anything especially for this host which is why the next two lines are commented
    #publicKey1 = RSA.importKey(base64.b64decode(ogPublicKey1))
    #cipherRSA1 = PKCS1_v1_5.new(publicKey1)

    publicKey2 = RSA.importKey(base64.b64decode(ogPublicKey2))
    cipherRSA2 = PKCS1_v1_5.new(publicKey2)

    conn1.sendline(publicKeyMITM)
    k = conn1.recv(4096)
    keyAES = cipherRSA_MITM.decrypt(base64.b64decode(k),s)
	
    conn2.sendline(base64.b64encode(cipherRSA2.encrypt(keyAES)))
    cur = 0
    while True :
        try :
            if (cur % 2 == 0): data = conn2.recv(4096)
            else : data = conn1.recv(4096)
            
            cipherAES = AES.new(keyAES,AES.MODE_CBC,base64.b64decode(data)[:16])
            r = cipherAES.decrypt(base64.b64decode(data)[16:])
            resultFile.write(r)

            if (cur % 2 == 0): conn1.sendline(data)
            else : conn2.sendline(data)
            cur += 1
        except:
            print("We've everything we need ! :)")
            break

conn1.close()
conn2.close()
