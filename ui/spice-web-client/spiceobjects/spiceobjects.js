/*
 eyeOS Spice Web Client
Copyright (c) 2015 eyeOS S.L.

Contact Jose Carlos Norte (jose@eyeos.com) for more information about this software.

This program is free software; you can redistribute it and/or modify it under
the terms of the GNU Affero General Public License version 3 as published by the
Free Software Foundation.
 
This program is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License for more
details.
 
You should have received a copy of the GNU Affero General Public License
version 3 along with this program in the file "LICENSE".  If not, see 
<http://www.gnu.org/licenses/agpl-3.0.txt>.
 
See www.eyeos.org for more details. All requests should be sent to licensing@eyeos.org
 
The interactive user interfaces in modified source and object code versions
of this program must display Appropriate Legal Notices, as required under
Section 5 of the GNU Affero General Public License version 3.
 
In accordance with Section 7(b) of the GNU Affero General Public License version 3,
these Appropriate Legal Notices must retain the display of the "Powered by
eyeos" logo and retain the original copyright notice. If the display of the 
logo is not reasonably feasible for technical reasons, the Appropriate Legal Notices
must display the words "Powered by eyeos" and retain the original copyright notice. 
 */

wdi.SpiceObject = {

    properties: {},

    //Methods to demarshall
    bytesToString: function (bytes, nbytes) {
        var result = '';
        var numBytes = nbytes || bytes.length;

        for (var i = 0; i < numBytes; i++) {
            result += String.fromCharCode(bytes.shift());
        }

        return result;
    },

    bytesToURI: function (data) {
        var blob = new Blob([data], {type: "image/jpeg"});
        return URL.createObjectURL(blob);
    },

    bytesToStringBE: function (bytes, nbytes) {
        var result = '';
        var numBytes = nbytes || bytes.length;

        for (var i = numBytes; i >= 0; i--) {
            result += String.fromCharCode(bytes[i]);
        }

        return result;
    },

    bytesToInt8: function (bytes) {
        return bytes.shift();
    },

    bytesToInt8NoAllocate: function (bytes) {
        var data = bytes.getByte(0);
        bytes.eatBytes(1);
        return data;
    },

    bytesToInt16: function (bytes) {
        var low = bytes.shift();
        var high = bytes.shift();

        return high * Math.pow(16, 2) + low;
    },

    bytesToInt16BE: function (bytes) {
        var high = bytes.shift();
        var low = bytes.shift();

        return high * Math.pow(16, 2) + low;
    },

    bytesToInt32: function (bytes) {
        var low = wdi.SpiceObject.bytesToInt16(bytes);
        var high = wdi.SpiceObject.bytesToInt16(bytes);

        return high * Math.pow(16, 4) + low;
    },

    bytesToInt16NoAllocate: function (bytes) {
        var low = bytes.getByte(0);
        var high = bytes.getByte(1);
        bytes.eatBytes(2);
        return high * Math.pow(16, 2) + low;
    },

    bytesToInt32NoAllocate: function (bytes) {
        var low = wdi.SpiceObject.bytesToInt16NoAllocate(bytes);
        var high = wdi.SpiceObject.bytesToInt16NoAllocate(bytes);
        return high * Math.pow(16, 4) + low;
    },

    bytesToInt32BE: function (bytes) {
        var high = wdi.SpiceObject.bytesToInt16BE(bytes);
        var low = wdi.SpiceObject.bytesToInt16BE(bytes);

        return high * Math.pow(16, 4) + low;
    },

    bytesToInt64: function (bytes) {
        var low = wdi.SpiceObject.bytesToInt32(bytes).toString(2).lpad('0', 32);
        var high = wdi.SpiceObject.bytesToInt32(bytes).toString(2).lpad('0', 32);

        return BigInteger.parse(high + low, 2);
    },

    bytesToInt64NoAllocate: function (bytes) {
        var low = wdi.SpiceObject.bytesToInt32NoAllocate(bytes).toString(2).lpad('0', 32);
        var high = wdi.SpiceObject.bytesToInt32NoAllocate(bytes).toString(2).lpad('0', 32);

        return BigInteger.parse(high + low, 2);
    },

    bytesToInt64BE: function (bytes) {
        var high = wdi.SpiceObject.bytesToInt32BE(bytes).toString(2).lpad('0', 32);
        var low = wdi.SpiceObject.bytesToInt32BE(bytes).toString(2).lpad('0', 32);

        return BigInteger.parse(high + low, 2);
    },

    bytesToArray: function (arr, blockSize, nblocks, endian) {
        var length = arr.length;
        var numBlocks = nblocks || length;
        var endianness = endian || 'LE';
        var numbers = [];
        var f = null;

        switch (blockSize) {
            case 8:
                f = wdi.SpiceObject.bytesToInt8;
                break;
            case 16:
                endianness == 'LE' ? f = wdi.SpiceObject.bytesToInt16 : f = wdi.SpiceObject.bytesToInt16BE;
                break;
            case 32:
                endianness == 'LE' ? f = wdi.SpiceObject.bytesToInt32 : f = wdi.SpiceObject.bytesToInt32BE;
                break;
            case 64:
                endianness == 'LE' ? f = wdi.SpiceObject.bytesToInt64 : f = wdi.SpiceObject.bytesToInt64BE;
                break;
            default:
                throw new Exception("Not supported number of bits", 1);
                return false;
        }

        for (var i = 0; i < numBlocks; i++) {
            numbers = numbers.concat(f(arr));
        }

        return numbers;
    },

    int32ToDouble: function (number) {
        var sInt = wdi.SpiceObject.unsignedToSigned(number >> 4);
        var decimals = (number & 0x0f) / 0x0f;
        var result = decimals + sInt;

        return result;
    },

    unsignedToSigned: function (number, stride) {
        //TODO: ugly?
        var maxBit = Math.pow(2, stride) - 1;
        if (number & Math.pow(2, stride - 1)) {
            number = -1 * (maxBit - number);
        }
        return number;
    },

    //Methods to marshall
    arrayToBytes: function (arr, blockSize, nblocks) {
        var length = arr.length;
        var numBlocks = nblocks || length;
        var f = null;
        var rawData = [];

        switch (blockSize) {
            case 8:
                f = wdi.SpiceObject.numberTo8;
                break;
            case 16:
                f = wdi.SpiceObject.numberTo16;
                break;
            case 32:
                f = wdi.SpiceObject.numberTo32;
                break;
            case 64:
                f = wdi.SpiceObject.numberTo64;
                break;
            default:
                throw new Exception("Not supported number of bits", 1);
                return false;
        }

        for (var i = 0; i < numBlocks; i++) {
            if (i <= length) {
                rawData = rawData.concat(f(arr[i]));
            } else {
                rawData.push(0x00);
            }
        }

        return rawData;
    },

    stringToBytes: function (string) {
        var length = string.length;
        var rawData = [];

        for (var i = 0; i < length; i++) {
            rawData.push(string.charCodeAt(i));
        }

        return rawData;
    },

    stringHexToBytes: function (string) {
        var length = string.length;
        var rawData = [];

        for (var i = 0; i < length; i += 2) {
            rawData.push(parseInt(string[i] + string[i + 1], 16));
        }

        return rawData;
    },

    stringBinaryToBytes: function (string, blocksize) {
        string = string.lpad('0', blocksize);
        var rawData = [];

        for (var i = blocksize; i >= 8; i -= 8) {
            rawData = rawData.concat(parseInt(string.substr(i - 8, 8), 2));
        }

        return rawData;
    },

    stringToBytesPadding: function (string, size) {
        var rawData = [];
        var strsize = string.length;

        for (var i = 0; i < size; i++) {
            if (size > strsize - 1) {
                rawData.push(0x00);
            } else {
                rawData.push(string.charCodeAt(i));
            }
        }

        return rawData;
    },

    numberTo64: function (biginteger) {
        var tmp = this.numberTo32((biginteger & 0xffffffffffffffff) >> 32);
        var tmp2 = this.numberTo32(biginteger & 0x00000000ffffffff);
        var rawData = tmp2.concat(tmp);
        return rawData;
    },

    numberTo32: function (number) {
        var rawData = new Array(3);

        for (var i = 0; i < 4; i++) {//iterations because of javascript number size
            rawData[i] = number & (255);//Get only the last byte
            number = number >> 8;//Remove the last byte
        }

        return rawData;
    },

    numberTo16: function (number) {
        var rawData = new Array(1);

        for (var i = 0; i < 2; i++) {
            rawData[i] = number & (255);
            number = number >> 8;
        }

        return rawData;
    },

    numberTo8: function (number) {
        return [number & (255)];
    },

    getMessageProperties: function () {
        return this.properties;
    },

    getMessageProperty: function (propName, defaultValue) {
        if (this.properties.hasOwnProperty(propName)) {
            return this.properties[propName];
        } else {
            return defaultValue;
        }
    }
};

wdi.SpiceDataHeader = $.spcExtend(wdi.SpiceObject, {
    objectSize:6,

    init: function(c) {
        c?this.setContent(c):false;
    },

    setContent: function(c) {
        //this.serial = c.serial;
        this.type = c.type;
        this.size = c.size;
        //this.sub_list = c.sub_list;
    },

    marshall: function() {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            //this.numberTo64(this.serial),
            this.numberTo16(this.type),
            this.numberTo32(this.size)
            //sthis.numberTo32(this.sub_list)W
        );
        return this.rawData;
    },

    demarshall: function(queue) {
        //this.serial = this.bytesToInt64(queue.shift(8));
        this.type = this.bytesToInt16NoAllocate(queue);
        this.size = this.bytesToInt32NoAllocate(queue);
        //this.sub_list = this.bytesToInt32(queue.shift(4));

        return this;
    }
});

wdi.SpiceLinkAuthMechanism = $.spcExtend(wdi.SpiceObject, {
    objectSize:4,

    init: function(c) {
        c?this.setContent(c):false;
    },

    setContent: function(c) {
        this.auth_mechanism = c.auth_mechanism;
    },

    marshall: function() {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.auth_mechanism)
        );
        return this.rawData;
    },

    demarshall: function(queue) {
        this.expectedSize = arguments[1] || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode:3});
        this.auth_mechanism = this.bytesToInt32NoAllocate(queue);
        'customDemarshall' in this?this.customDemarshall(queue):false;

        return this;
    }
});

wdi.SpiceLinkReply = $.spcExtend(wdi.SpiceObject, {
    objectSize:178,

    init: function(c) {
        c?this.setContent(c):false;
    },

    setContent: function(c) {
        this.error = c.error;
        this.pub_key = c.pub_key;
        this.num_common_caps = c.num_common_caps;
        this.num_channel_caps = c.num_channel_caps;
        this.caps_offset = c.caps_offset;
    },

    marshall: function() {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.error),
            this.arrayToBytes(this.pub_key, 8),
            this.numberTo32(this.num_common_caps),
            this.numberTo32(this.num_channel_caps),
            this.numberTo32(this.caps_offset)
        );
        return this.rawData;
    },

    demarshall: function(queue) {
        this.expectedSize = arguments[1] || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode:3});
        this.error = this.bytesToInt32NoAllocate(queue);
        this.pub_key = this.bytesToArray(queue.shift(this.expectedSize), 8);
        this.num_common_caps = this.bytesToInt32NoAllocate(queue);
        this.num_channel_caps = this.bytesToInt32NoAllocate(queue);
        this.caps_offset = this.bytesToInt32NoAllocate(queue);
        'customDemarshall' in this?this.customDemarshall(queue):false;

        return this;
    }
});

wdi.SpiceLinkEncryptedTicket = $.spcExtend(wdi.SpiceObject, {
    objectSize:128,

    init: function(c) {
        c?this.setContent(c):false;
    },

    setContent: function(c) {
        this.encrypted_data = c.encrypted_data;
    },

    marshall: function() {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.stringToBytes(this.encrypted_data, 8)
        );
        return this.rawData;
    },

    demarshall: function(queue) {
        this.expectedSize = arguments[1] || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode:3});
        this.encrypted_data = this.bytesToArray(queue.shift(this.expectedSize), 8);
        'customDemarshall' in this?this.customDemarshall(queue):false;

        return this;
    }
});

wdi.SpiceLinkMess = $.spcExtend(wdi.SpiceObject, {
    objectSize:18,

    init: function(c) {
        c?this.setContent(c):false;
    },

    setContent: function(c) {
        this.connection_id = c.connection_id;
        this.channel_type = c.channel_type;
        this.channel_id = c.channel_id;
        this.num_common_caps = c.num_common_caps;
        this.num_channel_caps = c.num_channel_caps;
        this.caps_offset = c.caps_offset;
        this.common_caps = c.common_caps;
        this.channel_caps = c.channel_caps;
    },

    marshall: function() {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.connection_id),
            this.numberTo8(this.channel_type),
            this.numberTo8(this.channel_id),
            this.numberTo32(this.num_common_caps),
            this.numberTo32(this.num_channel_caps),
            this.numberTo32(this.caps_offset)
        );
        if(this.num_common_caps > 0) {
            this.rawData = this.rawData.concat(this.numberTo32(this.common_caps));
        }
        if(this.num_channel_caps > 0) {
            this.rawData = this.rawData.concat(this.numberTo32(this.channel_caps));
        }
        return this.rawData;
    },

    demarshall: function(queue) {
        this.expectedSize = arguments[1] || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode:3});
        this.connection_id = this.bytesToInt32NoAllocate(queue);
        this.channel_type = this.bytesToInt8NoAllocate(queue);
        this.channel_id = this.bytesToInt8NoAllocate(queue);
        this.num_common_caps = this.bytesToInt32NoAllocate(queue);
        this.num_channel_caps = this.bytesToInt32NoAllocate(queue);
        this.caps_offset = this.bytesToInt32NoAllocate(queue);
        'customDemarshall' in this?this.customDemarshall(queue):false;

        return this;
    }
});

wdi.SpiceLinkHeader = $.spcExtend(wdi.SpiceObject, {
    objectSize:16,

    init: function(c) {
        c?this.setContent(c):false;
    },

    setContent: function(c) {
        this.magic = c.magic;
        this.major_version = c.major_version;
        this.minor_version = c.minor_version;
        this.size = c.size;
    },

    marshall: function() {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.magic),
            this.numberTo32(this.major_version),
            this.numberTo32(this.minor_version),
            this.numberTo32(this.size)
        );
        return this.rawData;
    },

    demarshall: function(queue) {
        this.expectedSize = arguments[1] || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode:3});
        this.magic = this.bytesToInt32NoAllocate(queue);
        this.major_version = this.bytesToInt32NoAllocate(queue);
        this.minor_version = this.bytesToInt32NoAllocate(queue);
        this.size = this.bytesToInt32NoAllocate(queue);
        'customDemarshall' in this?this.customDemarshall(queue):false;

        return this;
    }
});

wdi.RedMigrateData = $.spcExtend(wdi.SpiceObject, {
    objectSize: 0,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.vector = c.vector;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.arrayToBytes(this.vector, 8)
        );

        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});
        this.vector = this.bytesToArray(queue.shift(this.expectedSize), 8);
        

        return this;
    }
});

wdi.RedMainInit = $.spcExtend(wdi.SpiceObject, {
    objectSize: 32,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.session_id = c.session_id;
        this.display_channels_hint = c.display_channels_hint;
        this.supported_mouse_modes = c.supported_mouse_modes;
        this.current_mouse_mode = c.current_mouse_mode;
        this.agent_connected = c.agent_connected;
        this.agent_tokens = c.agent_tokens;
        this.multi_media_time = c.multi_media_time;
        this.ram_hint = c.ram_hint;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.session_id),
            this.numberTo32(this.display_channels_hint),
            this.numberTo32(this.supported_mouse_modes),
            this.numberTo32(this.current_mouse_mode),
            this.numberTo32(this.agent_connected),
            this.numberTo32(this.agent_tokens),
            this.numberTo32(this.multi_media_time),
            this.numberTo32(this.ram_hint)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});
        this.session_id = this.bytesToInt32NoAllocate(queue);
        this.display_channels_hint = this.bytesToInt32NoAllocate(queue);
        this.supported_mouse_modes = this.bytesToInt32NoAllocate(queue);
        this.current_mouse_mode = this.bytesToInt32NoAllocate(queue);
        this.agent_connected = this.bytesToInt32NoAllocate(queue);
        this.agent_tokens = this.bytesToInt32NoAllocate(queue);
        this.multi_media_time = this.bytesToInt32NoAllocate(queue);
        this.ram_hint = this.bytesToInt32NoAllocate(queue);
        

        return this;
    }
});

wdi.SpiceMsgMainAgentConnected = $.spcExtend(wdi.SpiceObject, {
    objectSize: 0,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {

    },



    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});
        

        return this;
    }
});

wdi.SpiceChannelsList = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.num_of_channels = c.num_of_channels;
        this.channels = c.channels;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.num_of_channels),
            this.arrayToBytes(this.channels, 16)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.num_of_channels = this.bytesToInt32NoAllocate(queue);
        this.channels = this.bytesToArray(queue.shift(this.expectedSize), 16);
        

        return this;
    }
});

wdi.RedSetAck = $.spcExtend(wdi.SpiceObject, {
    objectSize: 8,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.generation = c.generation;
        this.window = c.window;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.generation),
            this.numberTo32(this.window)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});
        this.generation = this.bytesToInt32NoAllocate(queue);
        this.window = this.bytesToInt32NoAllocate(queue);
        

        return this;
    }
});

//Exactly the same as RedPong
wdi.RedPing = $.spcExtend(wdi.SpiceObject, {
    objectSize: 12,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.id = c.id;
        this.time = c.time;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.id),
            this.numberTo64(this.time)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});
        this.id = this.bytesToInt32NoAllocate(queue);
        this.time = this.bytesToInt64NoAllocate(queue);

        if (this.expectedSize > 12) {
            queue.shift(this.expectedSize - 12);
        }


        return this;
    }
});

wdi.RedMigrate = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.flags = c.flags;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.flags)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});
        this.flags = this.bytesToInt32NoAllocate(queue);
        

        return this;
    }
});

wdi.RedWaitForChannel = $.spcExtend(wdi.SpiceObject, {
    objectSize: 10,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.type = c.type;
        this.id = c.id;
        this.serial = c.serial;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo8(this.type),
            this.numberTo8(this.id),
            this.numberTo64(this.serial)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});
        this.type = this.bytesToInt8NoAllocate(queue);
        this.id = this.bytesToInt8NoAllocate(queue);
        this.serial = this.bytesToInt64NoAllocate(queue);
        

        return this;
    }
});

wdi.RedWaitForChannels = $.spcExtend(wdi.SpiceObject, {
    objectSize: 1,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.wait_count = c.wait_count;
        this.wait_list = c.wait_list;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo8(this.wait_count),
            this.arrayToBytes(this.wait_list, 8)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});
        this.wait_count = this.bytesToInt8NoAllocate(queue);
        this.wait_list = this.bytesToArray(queue.shift(this.expectedSize), 8);
        

        return this;
    }
});

wdi.RedDisconnect = $.spcExtend(wdi.SpiceObject, {
    objectSize: 12,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.time_stamp = c.time_stamp;
        this.reason = c.reason;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo64(this.time_stamp),
            this.numberTo32(this.reason)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});
        this.time_stamp = this.bytesToInt64NoAllocate(queue);
        this.reason = this.bytesToInt32NoAllocate(queue);
        

        return this;
    }
});

wdi.RedMigrationBegin = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.port = c.port;
        this.sport = c.sport;
        this.host_name = c.host_name;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo16(this.port),
            this.numberTo16(this.sport),
            this.arrayToBytes(this.host_name, 8)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});
        this.port = this.bytesToInt16NoAllocate(queue);
        this.sport = this.bytesToInt16NoAllocate(queue);
        this.host_name = this.bytesToArray(queue.shift(this.expectedSize), 8);
        

        return this;
    }
});

wdi.RedNotify = $.spcExtend(wdi.SpiceObject, {
    objectSize: 25,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.time_stamp = c.time_stamp;
        this.severity = c.severity;
        this.visibility = c.visibility;
        this.what = c.what;
        this.message_len = c.message_len;
        this.message = c.message;
        this.zero = c.zero;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo64(this.time_stamp),
            this.numberTo32(this.severity),
            this.numberTo32(this.visibility),
            this.numberTo32(this.what),
            this.numberTo32(this.message_len),
            this.arrayToBytes(this.message, 8),
            this.numberTo8(this.zero)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});
        this.time_stamp = this.bytesToInt64NoAllocate(queue);
        this.severity = this.bytesToInt32NoAllocate(queue);
        this.visibility = this.bytesToInt32NoAllocate(queue);
        this.what = this.bytesToInt32NoAllocate(queue);
        this.message_len = this.bytesToInt32NoAllocate(queue);
        this.message = this.bytesToString(queue.shift(this.message_len));
        this.zero = this.bytesToInt8NoAllocate(queue);
        

        return this;
    }
});

wdi.RedMode = $.spcExtend(wdi.SpiceObject, {
    objectSize: 12,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.width = c.width;
        this.height = c.height;
        this.depth = c.depth;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.width),
            this.numberTo32(this.height),
            this.numberTo32(this.depth)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});
        this.width = this.bytesToInt32NoAllocate(queue);
        this.height = this.bytesToInt32NoAllocate(queue);
        this.depth = this.bytesToInt32NoAllocate(queue);
        

        return this;
    }
});

wdi.SpiceCDisplayInit = $.spcExtend(wdi.SpiceObject, {
    objectSize: 14,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.pixmap_cache_id = c.pixmap_cache_id;
        this.pixmap_cache_size = c.pixmap_cache_size;
        this.glz_dictionary_id = c.glz_dictionary_id;
        this.glz_dictionary_window_size = c.glz_dictionary_window_size;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo8(this.pixmap_cache_id),
            this.numberTo32(this.pixmap_cache_size),
            this.numberTo32(0),
            this.numberTo8(this.glz_dictionary_id),
            this.numberTo32(this.glz_dictionary_window_size)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.pixmap_cache_id = this.bytesToInt8NoAllocate(queue);
        this.pixmap_cache_size = this.bytesToInt64NoAllocate(queue);
        this.glz_dictionary_id = this.bytesToInt8NoAllocate(queue);
        this.glz_dictionary_window_size = this.bytesToInt32NoAllocate(queue);
        

        return this;
    }
});

wdi.SpiceSurfaceDestroy = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.surface_id = c.surface_id;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.surface_id)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.surface_id = this.bytesToInt32NoAllocate(queue);
        

        return this;
    }
});

wdi.SpiceSurface = $.spcExtend(wdi.SpiceObject, {
    objectSize: 20,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.surface_id = c.surface_id;
        this.width = c.width;
        this.height = c.height;
        this.format = c.format;
        this.flags = c.flags;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.surface_id),
            this.numberTo32(this.width),
            this.numberTo32(this.height),
            this.numberTo32(this.format),
            this.numberTo32(this.flags)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.surface_id = this.bytesToInt32NoAllocate(queue);
        this.width = this.bytesToInt32NoAllocate(queue);
        this.height = this.bytesToInt32NoAllocate(queue);
        this.format = this.bytesToInt32NoAllocate(queue);
        this.flags = this.bytesToInt32NoAllocate(queue);
        

        return this;
    }
});

wdi.SpicePath = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,


    marshall: function () {
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        var num = this.num_segments = this.bytesToInt32NoAllocate(queue);
        this.segments = [];

        for (var i= 0; i < num;i++) {
            this.segments[i] = new wdi.SpicePathSeg().demarshall(queue);
        }

        return this;
    }
});

wdi.SpicePathSeg = $.spcExtend(wdi.SpiceObject, {
    objectSize: 8,


    marshall: function () {
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.flags = this.bytesToInt8NoAllocate(queue);
        var count = this.count = this.bytesToInt32NoAllocate(queue);
        this.points = [];
        for(var i=0;i<count;i++) {
            this.points[i] = new wdi.SpicePointFix().demarshall(queue);
        }

        return this;
    }
});

wdi.SpicePoint = $.spcExtend(wdi.SpiceObject, {
    objectSize: 8,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.x = c.x;
        this.y = c.y;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.x),
            this.numberTo32(this.y)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.x = this.unsignedToSigned(this.bytesToInt32(queue.shift(4)), 32);
        this.y = this.unsignedToSigned(this.bytesToInt32(queue.shift(4)), 32);
        

        return this;
    }
});

wdi.SpicePoint16 = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.x = c.x;
        this.y = c.y;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo16(this.x),
            this.numberTo16(this.y)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.x = this.bytesToInt16NoAllocate(queue);
        this.y = this.bytesToInt16NoAllocate(queue);
        

        return this;
    }
});

wdi.SpicePointFix = $.spcExtend(wdi.SpiceObject, {
    objectSize: 8,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.x = c.hasOwnProperty('x') ? c.x : 0;
        this.y = c.hasOwnProperty('y') ? c.y : 0;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.x),
            this.numberTo32(this.y)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.x = this.int32ToDouble(this.bytesToInt32(queue.shift(4)), 32);
        this.y = this.int32ToDouble(this.bytesToInt32(queue.shift(4)), 32);
        

        return this;
    }
});

wdi.SpiceRect = $.spcExtend(wdi.SpiceObject, {
    objectSize: 16,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.top = c.top;
        this.left = c.left;
        this.bottom = c.bottom;
        this.right = c.right;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.top),
            this.numberTo32(this.left),
            this.numberTo32(this.bottom),
            this.numberTo32(this.right)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        //if (queue.getLength() < this.objectSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.top = this.bytesToInt32NoAllocate(queue);
        this.left = this.bytesToInt32NoAllocate(queue);
        this.bottom = this.bytesToInt32NoAllocate(queue);
        this.right = this.bytesToInt32NoAllocate(queue);

        return this;
    }
});

wdi.SpiceClipRects = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.num_rects = c.num_rects;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.num_rects)
        );
        for (var i = 0; i < this.num_rects; i++) {
            this.rawData = this.rawData.concat(this.rects[i].marshall());
        }

        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.num_rects = this.bytesToInt32NoAllocate(queue);

        if (this.num_rects > 0) {
            this.rects = [];
            for (var i = 0; i < this.num_rects; i++) {
                this.rects[i] = new wdi.SpiceRect().demarshall(queue);
            }
        }

        return this;
    }
});


wdi.SpiceClip = $.spcExtend(wdi.SpiceObject, {
    objectSize: 1,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.type = c.type;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo8(this.type)
        );
        if (this.type == wdi.SpiceClipType.SPICE_CLIP_TYPE_RECTS) {
            this.rawData = this.rawData.concat(
                this.rects.marshall()
            );
        }
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.type = this.bytesToInt8NoAllocate(queue);

        if (this.type == wdi.SpiceClipType.SPICE_CLIP_TYPE_RECTS) {
            this.rects = new wdi.SpiceClipRects().demarshall(queue);
        }
        return this;
    }
});

wdi.SpiceDisplayBase = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.surface_id = c.surface_id;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.surface_id),
            this.box.marshall(),
            this.clip.marshall()
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.surface_id = this.bytesToInt32NoAllocate(queue);
        this.box = new wdi.SpiceRect().demarshall(queue);
        this.clip = new wdi.SpiceClip().demarshall(queue);
        return this;
    }
});

wdi.SpiceQMask = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {

    },

    marshall: function () {
        var rawData = [];
        rawData = rawData.concat(
            this.numberTo8(this.flags),
            this.pos.marshall(),
            this.numberTo32(this.offset)
        );
        if (this.offset) {
            rawData = rawData.concat(
                this.image.marshall()
            );
        }
        return rawData;
    },

    demarshall: function (queue, expSize) {
        //in the timeline, demarshalling spiceqmask takes lot of time
        //and mask is not used anywhere in the code, its still unsupported
        //so we leave it commented until we realize whats a mask and why it takes sooooo long
        //to demarshall
        //to prevent the packet to not be contiguous, remove the bytes and leave
        queue.eatBytes(13); //the normal qmask size
        /*
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.flags = this.bytesToInt8NoAllocate(queue);
        this.pos = new wdi.SpicePoint().demarshall(queue);
        this.offset = this.bytesToInt32NoAllocate(queue);
        if (this.offset) {
            wdi.Debug.log('THERE IS A MASK IMAGE');
            var qdata = new wdi.ViewQueue();
            qdata.setData(queue.getDataOffset(this.offset));
            this.image = new wdi.SpiceImage().demarshall(qdata);
        }
        return this;
        */
    }
});

wdi.SpiceImageDescriptor = $.spcExtend(wdi.SpiceObject, {
    objectSize: 18,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {

    },

    marshall: function () {
        var rawData = [];
        rawData = rawData.concat(
            this.numberTo64(this.id),
            this.numberTo8(this.type),
            this.numberTo8(this.flags),
            this.numberTo32(this.width),
            this.numberTo32(this.height)
        );
        return rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        var id = this.bytesToInt32NoAllocate(queue);
        this.id = id.toString(16)+this.bytesToInt32NoAllocate(queue).toString(16);
        this.type = this.bytesToInt8NoAllocate(queue);
        this.flags = this.bytesToInt8NoAllocate(queue);
        this.width = this.bytesToInt32NoAllocate(queue);
        this.height = this.bytesToInt32NoAllocate(queue);
        this.offset = queue.getPosition();
        

        return this;
    }
});

wdi.SpiceImage = $.spcExtend(wdi.SpiceObject, {
    objectSize: 1,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {

    },

    marshall: function () {
        var rawData = [];
        rawData = rawData.concat(
            this.imageDescriptor.marshall(),
            this.data
        );
        return rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.imageDescriptor = new wdi.SpiceImageDescriptor().demarshall(queue);
        this.data = queue.getRawData();
        return this;
    }
});

wdi.SpiceDrawCopy = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    properties: {
        'overWriteScreenArea': true
    },

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.offset = c.offset;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.base.marshall(),
            this.numberTo32(this.offset),
            this.src_area.marshall(),
            this.numberTo16(this.rop_descriptor),
            this.numberTo8(this.scale_mode),
            this.mask.marshall(),
            this.image.marshall()
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.base = new wdi.SpiceDisplayBase().demarshall(queue);
        this.offset = this.bytesToInt32NoAllocate(queue);
        //this.src_bitmap = new wdi.SpiceImageDescriptor().demarshall(queue);
        this.src_area = new wdi.SpiceRect().demarshall(queue);
        this.rop_descriptor = this.bytesToInt16NoAllocate(queue);
        this.scale_mode = this.bytesToInt8NoAllocate(queue);
        this.mask = new wdi.SpiceQMask().demarshall(queue);


        //if offset equals to "at", then there is no need to adapt the queue!
        //this gives 10ms instead of 30ms in lot of situations
        if (queue.getPosition() == this.offset) {
            this.image = new wdi.SpiceImage().demarshall(queue);
        } else {
            var qdata = new wdi.ViewQueue();
            qdata.setData(queue.getDataOffset(this.offset));
            this.image = new wdi.SpiceImage().demarshall(qdata);
        }

        return this;
    }
});

wdi.drawBlend = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.base = c.base;
        this.alpha_flags = c.alpha_flags;
        this.alpha = c.alpha;
        this.offset = c.offset;
        this.src_area = c.src_area;
    },

    marshall: function () {
        var rawData = [];
        rawData = rawData.concat(
            this.base.marshall(),
            this.numberTo32(this.offset),
            this.src_area.marshall(),
            this.numberTo16(this.rop_descriptor),
            this.numberTo8(this.flags),
            this.mask.marshall(),
            this.image.marshall()
        );
        return rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.base = new wdi.SpiceDisplayBase().demarshall(queue);
        this.offset = this.bytesToInt32NoAllocate(queue);
        this.src_area = new wdi.SpiceRect().demarshall(queue);
        this.rop_descriptor = this.bytesToInt16NoAllocate(queue);
        this.flags = this.bytesToInt8NoAllocate(queue);
        this.mask = new wdi.SpiceQMask().demarshall(queue);

        this.image = new wdi.SpiceImage().demarshall(queue);
        return this;
    }
});

wdi.drawAlphaBlend = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.base = c.base;
        this.alpha_flags = c.alpha_flags;
        this.alpha = c.alpha;
        this.offset = c.offset;
        this.src_area = c.src_area;
    },



    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.base = new wdi.SpiceDisplayBase().demarshall(queue);
        this.alpha_flags = this.bytesToInt8NoAllocate(queue);
        this.alpha = this.bytesToInt8NoAllocate(queue);
        this.offset = this.bytesToInt32NoAllocate(queue);
        this.src_area = new wdi.SpiceRect().demarshall(queue);

        this.image = new wdi.SpiceImage().demarshall(queue);
        return this;
    }
});

wdi.drawTransparent = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {

    },



    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.base = new wdi.SpiceDisplayBase().demarshall(queue);
        this.offset = this.bytesToInt32NoAllocate(queue);
        this.src_area = new wdi.SpiceRect().demarshall(queue);
        this.transparent_color = new wdi.SpiceColor().demarshall(queue);
        this.transparent_true_color = new wdi.SpiceColor().demarshall(queue);
        this.image = new wdi.SpiceImage().demarshall(queue);
        return this;
    }
});

wdi.SpiceCopyBits = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.offset = c.offset;
    },

    marshall: function () {
        var rawData = [];
        rawData = rawData.concat(
            this.base.marshall(),
            this.src_position.marshall()
        );
        return rawData;

    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.base = new wdi.SpiceDisplayBase().demarshall(queue);
        this.src_position = new wdi.SpicePoint().demarshall(queue);
        return this;
    }
});

wdi.SpiceImageLZRGB = $.spcExtend(wdi.SpiceObject, {
    objectSize: 32,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {

    },



    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.length = this.bytesToInt32BE(queue.shift(4));
        this.magic = this.bytesToStringBE(queue.shift(4));
        this.version = this.bytesToInt32BE(queue.shift(4));
        this.type = this.bytesToInt32BE(queue.shift(4));
        this.width = this.bytesToInt32BE(queue.shift(4));
        this.height = this.bytesToInt32BE(queue.shift(4));
        this.stride = this.bytesToInt32BE(queue.shift(4));
        this.top_down = this.bytesToInt32BE(queue.shift(4));

        this.data = queue.shift(this.length);

        return this;
    }
});

wdi.SpiceMouseModeRequest = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.request_mode = c.request_mode;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.request_mode)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.request_mode = this.bytesToInt32NoAllocate(queue);
        

        return this;
    }
});

wdi.SpiceMouseMode = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.supported_modes = c.supported_modes;
        this.current_mode = c.current_mode;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.supported_modes),
            this.numberTo32(this.current_mode)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) return;
        this.supported_modes = this.bytesToInt16NoAllocate(queue);
        this.current_mode = this.bytesToInt16NoAllocate(queue);
        

        return this;
    }
});

wdi.RedcMousePress = $.spcExtend(wdi.SpiceObject, {
    objectSize: 3,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.button_id = c.button_id;
        this.buttons_state = c.buttons_state;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo8(this.button_id),
            this.numberTo16(this.buttons_state)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.button_id = this.bytesToInt8NoAllocate(queue);
        this.buttons_state = this.bytesToInt16NoAllocate(queue);
        

        return this;
    }
});

wdi.RedcMousePosition = $.spcExtend(wdi.SpiceObject, {
    objectSize: 11,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.x = c.x;
        this.y = c.y;
        this.buttons_state = c.buttons_state;
        this.display_id = c.display_id;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.x),
            this.numberTo32(this.y),
            this.numberTo16(this.buttons_state),
            this.numberTo8(this.display_id)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.x = this.bytesToInt32NoAllocate(queue);
        this.y = this.bytesToInt32NoAllocate(queue);
        this.buttons_state = this.bytesToInt16NoAllocate(queue);
        this.display_id = this.bytesToInt8NoAllocate(queue);
        

        return this;
    }
});

wdi.RedcMouseMotion = $.spcExtend(wdi.SpiceObject, {
    objectSize: 10,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.x = c.x;
        this.y = c.y;
        this.buttons_state = c.buttons_state;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.x),
            this.numberTo32(this.y),
            this.numberTo16(this.buttons_state)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.x = this.bytesToInt32NoAllocate(queue);
        this.y = this.bytesToInt32NoAllocate(queue);
        this.buttons_state = this.bytesToInt16NoAllocate(queue);
        

        return this;
    }
});

wdi.SpiceBrush = $.spcExtend(wdi.SpiceObject, {
    objectSize: 8,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.type = c.type;
        this.color = c.color;
    },



    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.type = this.bytesToInt8NoAllocate(queue);

        if (this.type == wdi.SpiceBrushType.SPICE_BRUSH_TYPE_PATTERN) {
            this.pattern = new wdi.SpicePattern().demarshall(queue);
        } else if (this.type == wdi.SpiceBrushType.SPICE_BRUSH_TYPE_SOLID) {
            this.color = new wdi.SpiceColor().demarshall(queue);
        }

        return this;
    }
});

wdi.SpiceColor = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {

    },

    marshall: function () {
        return [this.r, this.g, this.b];
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.data = this.bytesToInt32(queue.shift(4)) & 0xffffff; //make sure 24 bits, this is RGB888

        this.r = (this.data >> 16);
        this.g = ((this.data >> 8) & 0xff);
        this.b = (this.data & 0xff);

        this.html_color = "rgb(" + this.r + ", " + this.g + ", " + this.b + ")";

        var r = this.r.toString(16);
        var g = this.g.toString(16);
        var b = this.b.toString(16);

        if(r.length < 2) {
            r = '0'+r;
        }

        if(g.length < 2) {
            g = '0'+g;
        }

        if(b.length < 2) {
            b = '0'+b;
        }

        this.simple_html_color = '#'+r+g+b;
        return this;
    }
});

wdi.RgbaColor = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {

    },



    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.data = this.bytesToInt32(queue.shift(4)) & 0xffffffff; //make sure 32 bits, this is ARGB8888

        this.a = this.data >>> 24;
        this.r = (this.data >>> 16) & 0xff;
        this.g = (this.data >>> 8) & 0xff;
        this.b = this.data & 0xff;

        this.html_color = "rgb(" + this.r + ", " + this.g + ", " + this.b + ")";

        return this;
    }
});

wdi.SpicePattern = $.spcExtend(wdi.SpiceObject, {
    objectSize: 12,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {

    },



    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.offset = this.bytesToInt32NoAllocate(queue);
        this.point = new wdi.SpicePoint().demarshall(queue);
        var qdata = new wdi.ViewQueue();
        qdata.setData(queue.getDataOffset(this.offset));
        this.image = new wdi.SpiceImage().demarshall(qdata);

        return this;
    }
});

wdi.SpiceDrawFill = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    properties: {
        'overWriteScreenArea': true
    },

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.offset = c.offset;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.offset)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.base = new wdi.SpiceDisplayBase().demarshall(queue);
        this.brush = new wdi.SpiceBrush().demarshall(queue);
        this.rop_descriptor = this.bytesToInt16NoAllocate(queue);
        this.mask = new wdi.SpiceQMask().demarshall(queue);

        if (this.brush.type == wdi.SpiceBrushType.SPICE_BRUSH_TYPE_PATTERN) {
            this.brush.pattern.image = new wdi.SpiceImageDescriptor().demarshall(queue);
            this.brush.pattern.imageData = queue.getData();
        }
        return this;
    }
});

wdi.SpiceDrawRop3 = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,


    marshall: function () {
        var rawData = [];
        rawData = rawData.concat(
            this.base.marshall(),
            this.numberTo32(this.offset),
            this.src_area.marshall(),
            this.brush.marshall(),
            this.numberTo8(this.rop_descriptor),
            this.numberTo8(this.scale_mode),
            this.mask.marshall(),
            this.src_image.marshall()
        );
        if (this.brush.type == wdi.SpiceBrushType.SPICE_BRUSH_TYPE_PATTERN) {
            rawData = rawData.concat(
                this.brush.pattern.image.marshall(),
                this.brush.pattern.imageData
            );
        }
        return rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.base = new wdi.SpiceDisplayBase().demarshall(queue);
        this.offset = this.bytesToInt32NoAllocate(queue);
        this.src_area = new wdi.SpiceRect().demarshall(queue);
        this.brush = new wdi.SpiceBrush().demarshall(queue);
        this.rop_descriptor = this.bytesToInt8NoAllocate(queue);
        this.scale_mode = this.bytesToInt8NoAllocate(queue);
        this.mask = new wdi.SpiceQMask().demarshall(queue);
        this.src_image = new wdi.SpiceImage().demarshall(queue);

        if (this.brush.type == wdi.SpiceBrushType.SPICE_BRUSH_TYPE_PATTERN) {
            this.brush.pattern.image = new wdi.SpiceImageDescriptor().demarshall(queue);
            this.brush.pattern.imageData = queue.getData();
        }
        return this;
    }
});

wdi.SpiceDrawBlackness = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.offset = c.offset;
    },

    marshall: function () {
        var rawData = [];
        rawData = rawData.concat(
            this.base.marshall(),
            this.mask.marshall()
        );
        return rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.base = new wdi.SpiceDisplayBase().demarshall(queue);
        this.mask = new wdi.SpiceQMask().demarshall(queue);
        return this;
    }
});

wdi.SpiceDrawWhiteness = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.offset = c.offset;
    },

    marshall: function () {
        var rawData = [];
        rawData = rawData.concat(
            this.base.marshall(),
            this.mask.marshall()
        );
        return rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.base = new wdi.SpiceDisplayBase().demarshall(queue);
        this.mask = new wdi.SpiceQMask().demarshall(queue);
        return this;
    }
});

wdi.SpiceScanCode = $.spcExtend(wdi.SpiceObject, {
    objectSize: 1,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (scanCode) {
        this.code = scanCode || 0;
        this.zero = 0;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.arrayToBytes(this.code, 8),
            this.numberTo8(this.zero)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        return this;
    },

    getCode: function () {
        return this.code;
    }
});

wdi.RedCursorInit = $.spcExtend(wdi.SpiceObject, {
    objectSize: 9,


    marshall: function () {
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.position = new wdi.SpicePoint16().demarshall(queue);
        this.trail_length = this.bytesToInt16NoAllocate(queue);
        this.trail_frequency = this.bytesToInt16NoAllocate(queue);
        this.visible = this.bytesToInt8NoAllocate(queue);
        this.cursor = new wdi.RedCursor().demarshall(queue);
        

        return this;
    }
});

wdi.RedCursor = $.spcExtend(wdi.SpiceObject, {
    objectSize: 2,


    marshall: function () {
		this.rawData = [];
		this.rawData = this.rawData.concat(
			this.numberTo16(this.flags)
		);
		if(!(this.flags & 1)){
			this.rawData = this.rawData.concat(
				this.header.marshall(),
				this.data
			);
		}
		return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.flags = this.bytesToInt16NoAllocate(queue);

        this.header = null;
        this.data = null;

        if (!(this.flags & 1)) {
            this.header = new wdi.RedCursorHeader().demarshall(queue);
            this.data = queue.getData();
        }

        return this;
    }
});

wdi.RedCursorHeader = $.spcExtend(wdi.SpiceObject, {
    objectSize: 17,


    marshall: function () {
		this.rawData = [];
		this.rawData = this.rawData.concat(
			this.numberTo64(this.unique),
			this.numberTo8(this.type),
			this.numberTo16(this.width),
			this.numberTo16(this.height),
			this.numberTo16(this.hot_spot_x),
			this.numberTo16(this.hot_spot_y)
		);
		return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.unique = this.bytesToInt64NoAllocate(queue);
        this.type = this.bytesToInt8NoAllocate(queue);
        this.width = this.bytesToInt16NoAllocate(queue);
        this.height = this.bytesToInt16NoAllocate(queue);
        this.hot_spot_x = this.bytesToInt16NoAllocate(queue);
        this.hot_spot_y = this.bytesToInt16NoAllocate(queue);
        

        return this;
    }
});

wdi.RedCursorSet = $.spcExtend(wdi.SpiceObject, {
    objectSize: 5,

    marshall: function () {
		this.rawData = [];
		this.rawData = this.rawData.concat(
			this.position.marshall(),
			this.numberTo8(this.visible),
			this.cursor.marshall()
		);
		return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.position = new wdi.SpicePoint16().demarshall(queue);
        this.visible = this.bytesToInt8NoAllocate(queue);
        this.cursor = new wdi.RedCursor().demarshall(queue);

        return this;
    }
});

wdi.RasterGlyph = $.spcExtend(wdi.SpiceObject, {
    objectSize: 20,
    
    marshall: function () {
    },

    demarshall: function (queue, flags, numGlyphs) {
        var bpp = flags == 1 ? 1 : flags * 2;
        var result = [];

        for (var i = 0; i < numGlyphs; i++) {
            result[i] = {};
            result[i].render_pos = new wdi.SpicePoint().demarshall(queue);
            result[i].glyph_origin = new wdi.SpicePoint().demarshall(queue);
            result[i].width = this.bytesToInt16NoAllocate(queue);
            result[i].height = this.bytesToInt16NoAllocate(queue);
            result[i].data = queue.shift(result[i].height * Math.ceil(result[i].width * bpp / 8));
        }
        return result;
    }
});

wdi.GlyphString = $.spcExtend(wdi.SpiceObject, {
    objectSize: 3,

    marshall: function () {
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.len = this.bytesToInt16NoAllocate(queue);
        this.flags = this.bytesToInt8NoAllocate(queue);
        this.raster_glyph = new wdi.RasterGlyph().demarshall(queue, this.flags, this.len);
        

        return this;
    }
});

wdi.SpiceDrawText = $.spcExtend(wdi.SpiceObject, {
    objectSize: 8,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {

    },



    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.base = new wdi.SpiceDisplayBase().demarshall(queue);
        this.offset = this.bytesToInt32NoAllocate(queue);
        this.back_area = new wdi.SpiceRect().demarshall(queue);
        this.fore_brush = new wdi.SpiceBrush().demarshall(queue);
        this.back_brush = new wdi.SpiceBrush().demarshall(queue);
        this.fore_mode = this.bytesToInt16NoAllocate(queue);
        this.back_mode = this.bytesToInt16NoAllocate(queue);
        this.glyph_string = new wdi.GlyphString().demarshall(queue);
        return this;
    }
});

wdi.SpiceLineAttr = $.spcExtend(wdi.SpiceObject, {
    objectSize: 8,
    

    marshall: function () {
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.flags = this.bytesToInt8NoAllocate(queue);
        if (this.flags) {
            this.style_nseg = this.bytesToInt8NoAllocate(queue);
            this.style = this.int32ToDouble(this.bytesToInt32(queue.shift(4)));
        }

        return this;
    }
});

wdi.SpiceStroke = $.spcExtend(wdi.SpiceObject, {
    objectSize: 8,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {

    },

    marshall: function () {
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.base = new wdi.SpiceDisplayBase().demarshall(queue);
        this.offset = this.bytesToInt32NoAllocate(queue);
        this.attr = new wdi.SpiceLineAttr().demarshall(queue);
        this.brush = new wdi.SpiceBrush().demarshall(queue);
        this.fore_mode = this.bytesToInt16NoAllocate(queue);
        this.back_mode = this.bytesToInt16NoAllocate(queue);
        this.path = new wdi.SpicePath().demarshall(queue);
        return this;
    }
});


wdi.SpiceDrawInvers = $.spcExtend(wdi.SpiceObject, {
    objectSize: 8,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {

    },

    marshall: function () {
        var rawData = [];
        rawData = rawData.concat(
            this.base.marshall(),
            this.mask.marshall()
        );
        return rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.base = new wdi.SpiceDisplayBase().demarshall(queue);
        this.mask = new wdi.SpiceQMask().demarshall(queue);
        return this;
    }
});

wdi.SpiceStreamCreate = $.spcExtend(wdi.SpiceObject, {
    objectSize: 8,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {

    },

    marshall: function () {
        var rawData = [];
        rawData.concat(
            this.numberTo32(this.surface_id),
            this.numberTo32(this.id),
            this.numberTo8(this.flags),
            this.numberTo8(this.codec),
            this.numberTo64(this.stamp),
            this.numberTo32(this.stream_width),
            this.numberTo32(this.stream_height),
            this.numberTo32(this.src_width),
            this.numberTo32(this.src_height),
            this.rect.marshall(),
            this.clip.marshall()
        );
        return rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.surface_id = this.bytesToInt32NoAllocate(queue);
        this.id = this.bytesToInt32NoAllocate(queue);
        this.flags = this.bytesToInt8NoAllocate(queue);
        this.codec = this.bytesToInt8NoAllocate(queue);
        this.stamp = this.bytesToInt64NoAllocate(queue);
        this.stream_width = this.bytesToInt32NoAllocate(queue);
        this.stream_height = this.bytesToInt32NoAllocate(queue);
        this.src_width = this.bytesToInt32NoAllocate(queue);
        this.src_height = this.bytesToInt32NoAllocate(queue);
        this.rect = new wdi.SpiceRect().demarshall(queue);
        this.clip = new wdi.SpiceClip().demarshall(queue);
        return this;
    }
});

wdi.SpiceStreamDestroy = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {

    },

    marshall: function () {
        var rawData = [];
        rawData = rawData.concat(
            this.numberTo32(this.surface_id),
            this.numberTo32(this.id)
        );
        return rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.surface_id = this.bytesToInt32NoAllocate(queue);
        this.id = this.bytesToInt32NoAllocate(queue);
        return this;
    }
});

wdi.SpiceStreamData = $.spcExtend(wdi.SpiceObject, {
    objectSize: 8,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {

    },

    marshall: function () {
        var rawData = [];
        rawData = rawData.concat(
            this.numberTo32(this.id),
            this.numberTo32(this.multi_media_type),
            this.numberTo32(this.data_size),
            this.data
        );
        return rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.id = this.bytesToInt32NoAllocate(queue);
        this.multi_media_type = this.bytesToInt32NoAllocate(queue);
        this.data_size = this.bytesToInt32NoAllocate(queue);
        this.data = queue.getRawData();
        return this;
    }
});

wdi.SpiceStreamClip = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {

    },

    marshall: function () {
        var rawData = [];
        rawData = rawData.concat(
            this.numberTo32(this.id),
            this.clip.marshall()
        );
        return rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.id = this.bytesToInt32NoAllocate(queue);
        this.clip = new wdi.SpiceClip().demarshall(queue);
        return this;
    }
});

wdi.SpiceResourceList = $.spcExtend(wdi.SpiceObject, {
    objectSize: 2,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {

    },

    marshall: function () {
        var rawData = [];
        for (var i = 0; i < this.num_items; i++) {
            rawData = rawData.concat(
                this.numberTo8(this.items[i].type),
                this.numberTo64(this.items[i].id)
            );
        }
        return rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: 'Not enough queue to read', errorCode: 3});
        this.num_items = this.bytesToInt16NoAllocate(queue);
        this.items = [];
        for (var i = 0; i < this.num_items; i++) {
            this.items[i] = {
                type: this.bytesToInt8(queue.shift(1)),
                id: this.bytesToInt64(queue.shift(8))
            };
        }
        return this;
    }
});

wdi.SpiceMsgMainAgentTokens = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.num_tokens = c.num_tokens;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.num_tokens)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});
        this.num_tokens = this.bytesToInt32NoAllocate(queue);
        

        return this;
    }
});

wdi.SpiceMsgMainAgentDisconnected = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.error = c.error;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.error)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});
        this.error = this.bytesToInt32NoAllocate(queue);
        

        return this;
    }
});

wdi.SpiceMsgMainAgentData = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.agentMessage = c.agentMessage;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.agentMessage.marshall()
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});
        this.agentMessage = new wdi.VDAgentMessage().demarshall(queue);
        

        return this;
    }
});

wdi.VDIChunkHeader = $.spcExtend(wdi.SpiceObject, {
    objectSize: 8,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.port = c.port;
        this.size = c.size;
        this.packet = c.packet;
    },

    marshall: function () {
        this.rawData = [];
        var data = this.packet.marshall();
        this.rawData = this.rawData.concat(
            this.numberTo32(this.port),
            this.numberTo32(data.length),
            data
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});

        

        return this;
    }
});

wdi.VDAgentMessage = $.spcExtend(wdi.SpiceObject, {
    objectSize: 20,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.protocol = c.protocol;
        this.type = c.type;
        this.opaque = c.opaque;
        this.size = c.size;
        this.data = c.data;
    },

    marshall: function () {
        this.rawData = [];
        var data = this.data.marshall();
        this.rawData = this.rawData.concat(
            this.numberTo32(this.protocol),
            this.numberTo32(this.type),
            this.numberTo64(this.opaque),
            this.numberTo32(data.length),
            data
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});

        this.protocol = this.bytesToInt32NoAllocate(queue);
        this.type = this.bytesToInt32NoAllocate(queue);
        this.opaque = this.bytesToInt64NoAllocate(queue);
        this.size = this.bytesToInt32NoAllocate(queue);

        if (this.type == wdi.AgentMessageTypes.VD_AGENT_GET_WINDOWS_LIST) {
            var str = this.bytesToString(queue.shift(queue.length));
            if (str == "change") {
                this.window_list = str;
            } else {
                this.window_list = jQuery.parseJSON(str);
            }
        } else if(this.type == wdi.AgentMessageTypes.VD_AGENT_ANNOUNCE_CAPABILITIES) {
            this.caps = new wdi.VDAgentAnnounceCapabilities().demarshall(queue);
        } else if(this.type == wdi.AgentMessageTypes.VD_AGENT_CLIPBOARD_GRAB) {
            if(queue.getLength() == 0) {
                this.clipboardType = wdi.ClipBoardTypes.VD_AGENT_CLIPBOARD_NONE;
            } else {
                this.clipboardType = this.bytesToInt32NoAllocate(queue);
            }

        } else if(this.type == wdi.AgentMessageTypes.VD_AGENT_CLIPBOARD) {
            this.clipboardType = this.bytesToInt32NoAllocate(queue);
            this.clipboardData = this.bytesToString(queue.shift(queue.length));
        }

        

        return this;
    }
});

wdi.VDAgentHwndWindow = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.hwnd = c.hwnd;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.hwnd)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});

        

        return this;
    }
});

wdi.VDAgentMoveWindow = $.spcExtend(wdi.SpiceObject, {
    objectSize: 12,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.hwnd = c.hwnd;
        this.x = c.x;
        this.y = c.y;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.hwnd),
            this.numberTo32(this.x),
            this.numberTo32(this.y)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});

        

        return this;
    }
});

wdi.VDAgentResizeWindow = $.spcExtend(wdi.SpiceObject, {
    objectSize: 12,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.hwnd = c.hwnd;
        this.width = c.width;
        this.height = c.height;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.hwnd),
            this.numberTo32(this.width),
            this.numberTo32(this.height)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});

        

        return this;
    }
});

wdi.VDAgentMonitorsConfig = $.spcExtend(wdi.SpiceObject, {
    objectSize: 8,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.num_of_monitors = c.num_of_monitors;
        this.flags = c.flags;
        this.data = c.data;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.num_of_monitors),
            this.numberTo32(this.flags),
            this.data.marshall()
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});

        

        return this;
    }
});

wdi.VDAgentMonConfig = $.spcExtend(wdi.SpiceObject, {
    objectSize: 20,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.height = c.height;
        this.width = c.width;
        this.depth = c.depth;
        this.x = c.x;
        this.y = c.y;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.height),
            this.numberTo32(this.width),
            this.numberTo32(this.depth),
            this.numberTo32(this.x),
            this.numberTo32(this.y)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});

        

        return this;
    }
});

wdi.VDAgentAnnounceCapabilities = $.spcExtend(wdi.SpiceObject, {
    objectSize: 8,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.request = c.request;
        this.caps = c.caps;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.request),
            this.numberTo32(this.caps)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});

        this.request = this.bytesToInt32NoAllocate(queue);
        this.caps = this.bytesToInt32NoAllocate(queue);

        

        return this;
    }
});

wdi.VDAgentExecuteCommand = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.size = c.size;
        this.data = c.data;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.size),
            this.stringToBytes(this.data)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});

        

        return this;
    }
});

wdi.VDAgentClipboardRequest = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.type = c.type;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.type)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});

        this.type = this.bytesToInt32NoAllocate(queue);

        

        return this;
    }
});

wdi.VDAgentClipboardGrab = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.types = c.types;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.types)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});

        this.types = this.bytesToInt32NoAllocate(queue);

        

        return this;
    }
});

wdi.VDAgentClipboard = $.spcExtend(wdi.SpiceObject, {
    objectSize: 6,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.type = c.type;
        this.data = c.data;
    },

    marshall: function () {
        this.rawData = [];
        this.rawData = this.rawData.concat(
            this.numberTo32(this.type),
            this.stringToBytes(this.data)
        );
        return this.rawData;
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});

        this.type = this.bytesToInt32NoAllocate(queue);
        this.data = queue.getData();

        

        return this;
    }
});

wdi.PlaybackMode = $.spcExtend(wdi.SpiceObject, {
    objectSize: 6,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.multimedia_time = c.multimedia_time;
        this.audio_data_mode = c.audio_data_mode;
        this.data = c.data;
    },



    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});

        this.multimedia_time = this.bytesToInt32NoAllocate(queue);
        this.audio_data_mode = this.bytesToInt16NoAllocate(queue);
        this.data = queue.getData();
        

        return this;
    }
});

wdi.PlaybackStart = $.spcExtend(wdi.SpiceObject, {
    objectSize: 14,
    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.channels = c.channels;
        this.format = c.format;
        this.frequency = c.frequency;
        this.time = c.time;
    },



    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});

        this.channels = this.bytesToInt32NoAllocate(queue);
        this.format = this.bytesToInt16NoAllocate(queue);
        this.frequency = this.bytesToInt32NoAllocate(queue);
        this.time = this.bytesToInt32NoAllocate(queue);
        

        return this;
    }
});

wdi.PlaybackData = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.multimedia_time = c.multimedia_time;
        this.data = c.data;
    },



    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});

        this.multimedia_time = this.bytesToInt32NoAllocate(queue);
        this.data = queue.getData();
        

        return this;
    }
});

wdi.MainMultiMediaTime = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.multimedia_time = c.multimedia_time;
    },

    marshall: function () {
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});

        this.multimedia_time = this.bytesToInt32NoAllocate(queue);
        
        return this;
    }
});

wdi.PlaybackStop = $.spcExtend(wdi.SpiceObject, {
    objectSize: 0,




    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});

        return this;
    }
});

wdi.MainMChannelsList = $.spcExtend(wdi.SpiceObject, {
    objectSize: 4,

    init: function (c) {
        c ? this.setContent(c) : false;
    },

    setContent: function (c) {
        this.num_of_channels = c.num_of_channels;
    },

    marshall: function () {
    },

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});

        this.num_of_channels = this.bytesToInt32NoAllocate(queue);
        this.channels = [];
        var type = null;
        var id = null;
        for(var i = 0;i<this.num_of_channels;i++) {
            type = this.bytesToInt8NoAllocate(queue);
            id = this.bytesToInt8NoAllocate(queue);
            this.channels.push(type);
        }

        
        return this;
    }
});

wdi.SpiceDisplayInvalidAllPalettes = $.spcExtend(wdi.SpiceObject, {
    objectSize: 0,

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});
        
        return this;
    }
});

wdi.SpiceDisplayMark = $.spcExtend(wdi.SpiceObject, {
    objectSize: 0,

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});
        
        return this;
    }
});

wdi.SpiceDisplayReset = $.spcExtend(wdi.SpiceObject, {
    objectSize: 0,

    demarshall: function (queue, expSize) {
        this.expectedSize = expSize || this.objectSize;
        if (queue.getLength() < this.expectedSize) throw new wdi.Exception({message: "Not enough queue to read", errorCode: 3});
        
        return this;
    }
});

