rng = new SecureRandom();

function pack(source)

{

   var temp = "";

   for (var i = 0; i < source.length; i+=2)

   {

      temp+= String.fromCharCode(parseInt(source.substring(i, i + 2), 16));

   }

   return temp;

}
function char2hex(source)

{

   var hex = "";

   for (var i = 0; i < source.length; i+=1)

   {

      temp = source[i].toString(16);

      switch (temp.length)

      {

         case 1:

            temp = "0" + temp;

            break;

         case 0:

           temp = "00";

      }

      hex+= temp;

   }

   return hex;

}



function xor(a, b)

{

   length = Math.min(a.length, b.length);

   temp = "";

   for (var i = 0; i < length; i++)

   {

      temp+= String.fromCharCode(a.charCodeAt(i) ^ b.charCodeAt(i));

   }

   length = Math.max(a.length, b.length) - length;

   for (var i = 0; i < length; i++)

   {

      temp+= "\x00";

   }

   return temp;

}



function mgf1(mgfSeed, maskLen)

{

   t = "";

   hLen = 20;

   count = Math.ceil(maskLen / hLen);

   for (var i = 0; i < count; i++)

   {

      c = String.fromCharCode((i >> 24) & 0xFF, (i >> 16) & 0xFF, (i >> 8) & 0xFF, i & 0xFF);

      t+= pack(sha1Hash(mgfSeed + c));

   }



   return t.substring(0, maskLen);

}
function rsa_oaep_encrypt(message, n, e) {

        // precomputed values
        var k = 128; // length of n in bytes
        var hLen = 20;
        var mLen = message.length;
        var lHash = '\xda\x39\xa3\xee\x5e\x6b\x4b\x0d\x32\x55\xbf\xef\x95\x60\x18\x90\xaf\xd8\x07\x09'; // pack(sha1Hash(""))
        var temp = k - mLen - 2 * hLen - 2;

        for (var i = 0; i < temp; i++) {
            lHash += '\x00';
        }

        var db = lHash + '\x01' + message;

        var seed = '';
        for (var i = 0; i < hLen + 4; i += 4) {
            temp = new Array(4);
            rng.nextBytes(temp);
            seed += String.fromCharCode(temp[0], temp[1], temp[2], temp[3]);
        }
        seed = seed.substring(4 - seed.length % 4);

        var dbMask = mgf1(seed, k - hLen - 1);
        var maskedDB = xor(db, dbMask);
        var seedMask = mgf1(maskedDB, hLen);
        var maskedSeed = xor(seed, seedMask);
        var em = "\x00" + maskedSeed + maskedDB;

        m = new Array();
        for (i = 0; i < em.length; i++) {
            m[i] = em.charCodeAt(i);
        }
        m = new encryptionBigInteger(m, 256);
        c = m.modPowInt(e, n); // doPublic
        c = c.toString(16);

        if (c.length & 1)
            c = "0" + c;

        return c;
    }


function RSA_public_encrypt(password, pub_key) {

        var keyInChar = new Uint8Array(pub_key);
        var rawPubKey = new Array(129); // 00xxx

        for (var i = 0; i < 129; i++)
            rawPubKey[i] = keyInChar[28 + i];

        var n = new encryptionBigInteger(rawPubKey);
        var e = new encryptionBigInteger('010001', 16);

        var hexRsa = rsa_oaep_encrypt(password + String.fromCharCode(0), n, e);
        return hexRsa;
    }
