import sys
import PySimpleGUI as sg 
from loguru import logger

import smtplib, ssl
from email.message import EmailMessage
from email.mime.text import MIMEText
from email.header import Header

from typing import NamedTuple

import time
import random

import codecs
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend

import configparser

class Contact(NamedTuple):
    courrielStr: str
    prenomStr: str

def main(debug: bool):

    if not debug:
        logger.remove()
        logger.add(sys.stderr, level="INFO")

    choices = ('Appel', 'Mot de passe', 'Rencontre', 'Référence', 'Bienvenue', 'Premier avis', 'Deuxième avis', 'Profil désactivé', 'Cotisation', 'Photo acceptée', 'Photo refusée')
    layout = [  [sg.Text("Ajouter les contacts 'prenom.nom@domaine.com:Prénom;prenom2.nom@domaine.com:Prénom2;prenom3.nom@domaine.com:Prénom3;'")],
                [sg.Text("Puis sélectionner le type d'envoi de courriel massif")],            
                [sg.Multiline(key="emails", size=(100, 20)), sg.Listbox(choices, size=(15, len(choices)), key='mailType')],            
                [sg.Button("Exécuter")],
                [sg.Text("L'envoi des courriels peut prendre un certain temps car un délai est ajouté pour contourner la surveillance spam de Google.", key='log')],
                [sg.Text("", key='spacer')],
                [sg.Text("Envoyer les questions à info@becs.ca", font=("Arial", 7))] ]
    window = sg.Window('BecsCourrier', icon='./img/becs.ico').Layout(layout)                                               
   
    while True:
        event, values = window.read()        
        if event == sg.WIN_CLOSED:
            break
        else:
            if event == "Exécuter":
                window["log"].update("Envoi massif des courriel exécuté avec succès.") 

            sendToStr = values["emails"]
            emailTypeStr = values["mailType"]
            if sendToStr is None or not sendToStr:
                window["log"].update("Aucun courriel fourni. Aucun envoi.")  
            elif emailTypeStr is None or not emailTypeStr:     
                window["log"].update("Aucun type de courriel sélectionné. Aucun envoi.")    
            else:
                contactList = []
                start_index: int = 0
                while start_index < len(sendToStr):
                    end_index = sendToStr.find(':', start_index)
                    if end_index == -1:
                        break
                    courrielStr = sendToStr[start_index:end_index]
                    start_index = end_index + 1
                    end_index = sendToStr.find(';', start_index)
                    if end_index == -1:
                        break
                    nameStr = sendToStr[start_index:end_index]
                    contactList.append(Contact(courrielStr, nameStr))
                    start_index = end_index + 1

                for contactObj in contactList:
                    sendMail(contactObj.courrielStr, contactObj.prenomStr, emailTypeStr[0])
                    time.sleep(random.randrange(1,4)) #in seconds

    window.close() 

def sendMail(receiverStr: str, prenomStr: str, emailTypeStr: str):
    port = 465
    smtp_server = "smtp.gmail.com"    
    encryptedPasswordStr = "8c13e3bd7a3e5d59957e93bda090541a877b74eee52451265fce817d553cf0ff"
    senderStr = "infobecs.contact@gmail.com"

    msg = EmailMessage()
    msg['From'] = senderStr
    msg['To'] = receiverStr

    msg['Subject'] = "Bonjour " + prenomStr    

    file = open(getHtmlFile(emailTypeStr), mode='r', encoding="utf-8")
    bodyHtmlStr = file.read()
    file.close()    
    bodyStr = MIMEText(bodyHtmlStr, "html", 'utf-8')
    msg.set_content(bodyStr)

    config = configparser.ConfigParser()
    config.read('./config/config.ini')
    keyStr = config.get('DEFAULT','key')
    ivStr = config.get('DEFAULT','iv')

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
        server.login(senderStr, decrypt(keyStr, ivStr, encryptedPasswordStr))
        server.send_message(msg, from_addr=senderStr, to_addrs=receiverStr)      

def getHtmlFile(emailTypeStr: str):
    if emailTypeStr == 'Appel':
        return "./html/membres.appel.html"
    elif emailTypeStr == 'Mot de passe':
        return "./html/mdp.recuperer.html"
    elif emailTypeStr == 'Rencontre':
        return "./html/rencontre.demande.html"
    elif emailTypeStr == 'Référence':
        return "./html/reference.html"
    elif emailTypeStr == 'Bienvenue':
        return "./html/bienvenue.html"
    elif emailTypeStr == 'Premier avis':
        return "./html/renouvellement.avis1.html"
    elif emailTypeStr == 'Deuxième avis':
        return "./html/renouvellement.avis2.html"
    elif emailTypeStr == 'Profil désactivé':
        return "./html/profil.desactiver.html"
    elif emailTypeStr == 'Cotisation':
        return "./html/cotisation.reception.html"
    elif emailTypeStr == 'Photo acceptée':
        return "./html/photo.accepter.html"
    elif emailTypeStr == 'Photo refusée':
        return "./html/tx.refuser.html"
    return ""

def decrypt(key_aslatin1, iv, msg_as_ascii_hex):
    msg = codecs.decode(msg_as_ascii_hex, "hex")
    key = key_aslatin1.encode("latin1")
    ivBinary = iv.encode("latin1")
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.CBC(ivBinary), backend=backend)
    decryptor = cipher.decryptor()
    rslt_bytes = decryptor.update(msg) + decryptor.finalize()
    rslt = rslt_bytes.decode("utf8")
    return rslt

if __name__ == "__main__":
    main(True)
