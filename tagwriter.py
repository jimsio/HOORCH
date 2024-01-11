#!/usr/bin/env python3
# -*- coding: UTF8 -*-

import sys
import time
import unicodedata
import board
import busio
from adafruit_pn532.spi import PN532_SPI
from adafruit_pn532.adafruit_pn532 import MIFARE_CMD_AUTH_B
from digitalio import DigitalInOut
import ndef
import leds
import audio

# gpio24
reader1_pin = DigitalInOut(board.D24)

reader = []

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)

reader.append(PN532_SPI(spi, reader1_pin, debug=False))
# ic, ver, rev, support = reader[0].firmware_version
reader[0].SAM_configuration()

path = "./figure_ids.txt"
file = open(path, mode="r", encoding="utf-8")
figures = file.readlines()
file.close()

figure_database = []

#nftools franziseppi 00:00:03:!12!:D1:01:0E:54:02:65:6E:66:72:61:6E:7A
prefix = b'\x00\x00\x03'
#length_ndef_msg = b''
#record_header = b'\xD1'
#length_rec_type_field = b'\x01'
#payload_length = b'\'
#record_type = b'\x54'
#encoding = b'\x02' #utf8 and length of language code
#language = b'\x65\x6E'
suffix = b'\xFE'


#https://community.element14.com/challenges-projects/project14/nfc-rfid/b/blog/posts/nfc-badge---update-your-badge-with-your-smartphone---ndef-and-app
#00 00 - nur für mifare!
#x03 = TLV Block tag field - 0x03=NDEF message
#!12! = length of the NDEF message 12 = 18 Bytes )
#--ndef record starts here
#xD1 = record header 0xD1= Well-Known Record
#01 = length of record type field
#0E = payload length (OE = 14 Bytes)
#54 = Record Type 0x54=Text Record
#--- here starts the payload ---
#02 = encoding (UTF8) and length of language code (2 bytes)
#65+6E = language code (en) - others: 64+65 (de)
#66:72:61:6E:7A = text string
#--- end payload ---
#--ndef record ends here
#FE - Terminator Last TLV block / suffix

key = b'\xFF\xFF\xFF\xFF\xFF\xFF'

#write single word to ntag2 (sticker), mifare (cards, chips) not supported yet
#max length of word is 20!
def write_single(word):
    leds.reset()  # reset leds
    leds.switch_on_with_color(0)
    
    print("Place tag on reader1. Will write this to tag: "+str(word))
    #audio.espeaker("Schreibe "+str(word) +
    #               " auf den Täg. Bitte Täg auf Spielfeld 1 platzieren")
    time.sleep(2)
    tag_uid = reader[0].read_passive_target(timeout=0.2)

    if tag_uid:
        # bytearray(b'\x04q\x1b\xea\xa0e\x80')
        #print(tag_uid)

        id_readable = ""

        for counter, number in enumerate(tag_uid):
            if counter < 4:
                id_readable += str(number)+"-"
            else:
                id_readable = id_readable[:-1]
                break
        
        print("write "+str(word) + " on tag with tag_uid: " + id_readable)
        
        #record = ndef.TextRecord("frau12345","en")
        #en defines language, english
        record = ndef.TextRecord(word,"en")
        payload = b''.join(ndef.message_encoder([record]))
        #b'\xd1\x01\x0eT\x02enfranziseppi'

        #payload + encoding + langauge code (en)
        #payload_length = hex(len(payload)+3)
        #length_ndef_msg = hex(len(payload)+7)
        #full_payload = prefix+length_ndef_msg+length_rec_type_field+payload_length+record_type+encoding+language+suffix
        length_ndef_msg = bytearray.fromhex(hex(len(payload))[2:]) #16 = b'\x10'
        full_payload = prefix+length_ndef_msg+payload+suffix

        data = bytearray(32)
        data[0:len(full_payload)] = full_payload
        
        chunks = len(full_payload)
        
        verify_data = bytearray(0)

        #mifare tags

        #mifare 1K layout (chip + card)
        # 1 kByte
        # 16 Sektoren zu je 4 Blöcken (16 Bytes/16 Ascii Characters pro Block)

        #writeable blocks (https://support.ccs.com.ph/portal/en/kb/articles/mifare-classic-1k-memory-structure)
        # 4, 5, 6
        # 8, 9, 0A,
        # 0C, 0D, 0E,...
        if id_readable.endswith("-"):
            id_readable = id_readable[:-1]

            chunk_size = 16
            send = [data[i:i+chunk_size] for i in range(0, chunks, chunk_size)]
            
            #write 16 bytes to blocks 4 and 5
            for i, s in enumerate(send):
                print("Authenticating block "+str(4+i))
                authenticated = reader[0].mifare_classic_authenticate_block(tag_uid, 4+i, MIFARE_CMD_AUTH_B, key)
                if not authenticated:
                    print("Authentication failed!")
                
                reader[0].mifare_classic_write_block(4+i, s)

                # Read blocks
                print("Wrote to block "+str(4+i))
                #print("Now reading")
                verify_data.extend(reader[0].mifare_classic_read_block(4+i))

        #ntag2 tags
        else:
            #remove two \x00 \x00 from prefix - not needed for ntag2
            data = bytearray(32)
            data[0:len(data)-2] = data[2:]
            print(data)
            #error
            #bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00ann12345')

            chunk_size = 4
            send = [data[i:i+chunk_size] for i in range(0, chunks, chunk_size)]

            #write 4 bytes to blocks 4 to 12
            for i, s in enumerate(send):
                j = reader[0].ntag2xx_write_block(4+i, s)

            time.sleep(0.5)

            # Read blocks

            #reads until block 12, means 8 block x 4 byte = 32 bytes/ascii characters
            for i in range(4, 12):
                verify_data.extend(reader[0].ntag2xx_read_block(i))

        print(verify_data)
        if verify_data == data:
            print("successfully wrote "+str(word)+" to tag")
            audio.espeaker("Schreiben erfolgreich, Füge Täg zu Datenbank hinzu")

            db_file = open('figure_db.txt', 'a')
            # 12-56-128-34;ritter
            db_file.write(id_readable+";"+word+"\n")
            db_file.close()
        else:
            print("error occured while writing, try again.")

    else:
        print("no tag on rfid reader")
        audio.espeaker(
            "Du hast keinen Täg auf das Spielfeld platziert. Täg wurde nicht beschrieben.")


def write_set():
    audio.espeaker(
        "Wir beschreiben das gesamte Spieleset. Stelle die Figuren bei Aufruf auf Spielfeld 1")
    leds.reset()  # reset leds
    leds.switch_on_with_color(0)

    mifare = False

    for figure in figures:
        # remove /n at the end - file figure_ids.txt needs an empty line at the end
        figure = figure[:figure.find("\n")]

        if figure == "+":
            audio.espeaker("Nächster Abschnitt")
            figure_database.append(["", ""])
            continue

        else:
            valid = False

            while not valid:

                tag_uid = None
                id_readable = ""

                audio.espeaker("Nächster Figur:")
                audio.espeaker(figure)
                audio.espeaker("Figur stehen lassen")

                while not tag_uid:
                    tag_uid = reader[0].read_passive_target(timeout=1.0)

                # write_on_tag(tag_uid, text)

                for counter, number in enumerate(tag_uid):
                    if counter < 4:
                        id_readable += str(number)+"-"
                    else:
                        id_readable = id_readable[:-1]
                        break

                # reader has issues with reading mifare cards, stick with the tag_uid
                if id_readable.endswith("-"):
                    print("mifare chip!")
                    id_readable = id_readable[:-1]
                    mifare = True

                print(id_readable)

                if not mifare:
                    # write
                    message = lang+figure+endofmessage
                    print("message: " + str(message))
                    chunks, chunk_size = len(message), 4
                    send = [message[i:i+chunk_size]
                            for i in range(0, chunks, chunk_size)]
                    # print(send)

                    for i, s in enumerate(send):
                        while len(s) != 4:
                            s += "#"

                        k = 0

                        while not reader[0].ntag2xx_write_block(7+i, s.encode()):
                            print(
                                "Failed to write {0} to at block {1}.".format(s, 7+i))

                            k += 1

                            if k == 6:
                                print(
                                    "To many false writings. Terminate for this tag block. try-block will start loop for this tag again")
                                break

                    time.sleep(0.5)

                    # read for verification
                    read_message = ""

                    breaker = False

                    try:
                        for i in range(7, 14):
                            block = reader[0].ntag2xx_read_block(i)
                            print(block)
                            for character in block:
                                if character != ord(endofmessage):
                                    read_message += chr(character)
                                else:
                                    breaker = True
                                    break

                            if breaker:
                                break

                        # remove unicode control characters from read string
                        read_message = "".join(
                            ch for ch in read_message if unicodedata.category(ch)[0] != "C")

                        # enFRAGEZEICHEN#
                        message = message[2:-1]
                        # read_message has no #/endofmessage at end, this was checked during reading
                        read_message = read_message[2:]

                    # if tag was removed before it was properly read
                    except TypeError:
                        print(
                            "Error while reading RFID-tag content. Tag was probably removed before reading was completed.")
                        # audio.espeaker("Täg konnte nicht gelesen werden. Lass ihn länger auf dem Feld stehen!")
                        # Die Figur konnte nicht erkannt werden. Lass sie länger auf dem Feld stehen.
                        audio.play_full("TTS", 199)

                    valid = message == read_message
                    print("valid " + str(valid))

                else:
                    valid = True

            figure_database.append([id_readable, figure])
            print("added figure to figure db")

    leds.reset()
    audio.espeaker("Ende der Datei erreicht, schreibe die Datenbank")

    db_file = open('figure_db.txt', 'w')
    for pair in figure_database:
        # 12-56-128-34;ritter
        db_file.write(str(pair[0])+";"+str(pair[1])+"\n")

    db_file.close()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        write_single(sys.argv[1])
    else:
        write_set()
