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

//Sandboxed script without access to other external functions, objects or anything.
//used for webworkers.
//includes: quic and lz_rgb

window = this;
if (!window['wdi']) {
	window['wdi'] = {};
}

window['wdi'].WorkerOperations = {
	quic: 0,
	lz_rgb: 1,
	bytesToUriJpeg: 2,
	bytesToUriPng: 3
};

function dispatch(arr, useMessage) {

	var u8 = new Uint8Array(arr);
	var postMessageW3CCompilant = u8[3];


	var result = null;
	var operation = u8[0];

	if (operation === wdi.WorkerOperations.quic) {
		try {
			result = wdi.JSQuic.quic_decode(arr);
		} catch (e) {

		}
	} else if (operation === wdi.WorkerOperations.lz_rgb) { //lz?
		try {
			result = wdi.LZSS.lz_rgb32_decompress_rgb(arr);
		} catch (e) {

		}
	} else if (operation === wdi.WorkerOperations.bytesToUriJpeg) {
		try {
			result = bytesToURI(u8, 'jpeg');
			self.postMessage(result);
			return; //string is not transferable!
		} catch (e) {

		}
	} else if (operation === wdi.WorkerOperations.bytesToUriPng) {
		try {
			result = bytesToURI(u8, 'png');
			self.postMessage(result);
			return; //string is not transferable!
		} catch (e) {

		}
	}
	if (useMessage && result) {

		if (postMessageW3CCompilant) {
			self.postMessage(result, [result]);
		} else {
			self.postMessage(result);
		}

	} else {
		return result;
	}

}

window['workerDispatch'] = dispatch;

self.addEventListener('message', function(e) {
	return dispatch(e.data, true);
}, false);



//bytes to uri
function bytesToURI(data, type) {
	var tmpstr = 'data:image/'+type+',';
	var len = data.length;
	for (var i = 4; i < len; i++) {
		if (data[i] < 16) {
			tmpstr += '%0';
		} else {
			tmpstr += '%';
		}
		tmpstr += data[i].toString(16);
	}

	return tmpstr;
}


//quic


wdi.QuicImageType = {
	QUIC_IMAGE_TYPE_INVALID: 0,
	QUIC_IMAGE_TYPE_GRAY: 1,
	QUIC_IMAGE_TYPE_RGB16: 2,
	QUIC_IMAGE_TYPE_RGB24: 3,
	QUIC_IMAGE_TYPE_RGB32: 4,
	QUIC_IMAGE_TYPE_RGBA: 5
};

function bytesToInt16(bytes) {
	var low = bytes.shift();
	var high = bytes.shift();

	return high * Math.pow(16, 2) + low;
}

function bytesToInt32(bytes) {
	var low = bytesToInt16(bytes);
	var high = bytesToInt16(bytes);

	return high * Math.pow(16, 4) + low;
}

wdi.quic = {};

function wdi_quic_QuicFamily() {
	this.notGRcwlen = [];
	this.nGRcodewords = [];
	this.notGRprefixmask = [];
	this.notGRsuffixlen = [];
	this.xlatU2L = [];
	this.xlatL2U = [];
}

function wdi_quic_s_bucket() {
	this.pcounters = null;
	this.bestcode = 0;
}

function wdi_quic_CommonState() {
	this.wm_trigger = this;
	this.encoder = null;
	this.waitcnt = 0;
	this.tabrand_seed = wdi.JSQuic.stabrand();
	this.wmidx = wdi.JSQuic.DEFwmistart;
	this.wmileft = wdi.JSQuic.wminext;
	wdi.JSQuic.set_wm_trigger(this);


	this.melcstate = 0;
	this.melclen = wdi.JSQuic.J[0];
	this.melcorder = (1 << this.melclen) >>> 0;
}


function wdi_quic_FamilyStat() {
	this.buckets_buf = null;
	this.buckets_ptrs = null;
	this.counters = 0;
}

function wdi_quic_Channel() {
	this.encoder = null;
	this.correlate_row_width = 0;
	this.correlate_row = null;

	this._buckets_ptrs = null;

	this.family_stat_8bpc = new wdi_quic_FamilyStat();
	this.family_stat_5bpc = new wdi_quic_FamilyStat();

	this.state = new wdi_quic_CommonState();
	this.oldFirst = 0;
}

wdi.JSQuic = {
	QUIC_MAGIC: 1364543811, //"QUIC"
	MAXNUMCODES: 8,

	DEFevol: 3,
	MINevol: 0,
	MAXevol: 5,

	DEFwmistart: 0,
	MINwmistart: 0,

	DEFmaxclen: 26,

	DEFwmimax: 6,

	DEFwminext: 2048,
	MINwminext: 1,
	MAXwminext: 100000000,
	MAX_CHANNELS: 4,

	wmimax: 6,

	wminext: 2048,

	evol: 3,
	family_8bpc: new wdi_quic_QuicFamily(),
	family_5bpc: new wdi_quic_QuicFamily(),

	bppmask: new Int32Array([
		0x00000000,
		0x00000001, 0x00000003, 0x00000007, 0x0000000f,
		0x0000001f, 0x0000003f, 0x0000007f, 0x000000ff,
		0x000001ff, 0x000003ff, 0x000007ff, 0x00000fff,
		0x00001fff, 0x00003fff, 0x00007fff, 0x0000ffff,
		0x0001ffff, 0x0003ffff, 0x0007ffff, 0x000fffff,
		0x001fffff, 0x003fffff, 0x007fffff, 0x00ffffff,
		0x01ffffff, 0x03ffffff, 0x07ffffff, 0x0fffffff,
		0x1fffffff, 0x3fffffff, 0x7fffffff, 0xffffffff
	]),

	bitat: new Int32Array([
		0x00000001, 0x00000002, 0x00000004, 0x00000008,
		0x00000010, 0x00000020, 0x00000040, 0x00000080,
		0x00000100, 0x00000200, 0x00000400, 0x00000800,
		0x00001000, 0x00002000, 0x00004000, 0x00008000,
		0x00010000, 0x00020000, 0x00040000, 0x00080000,
		0x00100000, 0x00200000, 0x00400000, 0x00800000,
		0x01000000, 0x02000000, 0x04000000, 0x08000000,
		0x10000000, 0x20000000, 0x40000000, 0x80000000
	]),

	TABRAND_TABSIZE: 256,
	TABRAND_SEEDMASK: 0x0ff,

	tabrand_chaos: new Int32Array([
		0x02c57542, 0x35427717, 0x2f5a2153, 0x9244f155, 0x7bd26d07, 0x354c6052, 0x57329b28, 0x2993868e,
		0x6cd8808c, 0x147b46e0, 0x99db66af, 0xe32b4cac, 0x1b671264, 0x9d433486, 0x62a4c192, 0x06089a4b,
		0x9e3dce44, 0xdaabee13, 0x222425ea, 0xa46f331d, 0xcd589250, 0x8bb81d7f, 0xc8b736b9, 0x35948d33,
		0xd7ac7fd0, 0x5fbe2803, 0x2cfbc105, 0x013dbc4e, 0x7a37820f, 0x39f88e9e, 0xedd58794, 0xc5076689,
		0xfcada5a4, 0x64c2f46d, 0xb3ba3243, 0x8974b4f9, 0x5a05aebd, 0x20afcd00, 0x39e2b008, 0x88a18a45,
		0x600bde29, 0xf3971ace, 0xf37b0a6b, 0x7041495b, 0x70b707ab, 0x06beffbb, 0x4206051f, 0xe13c4ee3,
		0xc1a78327, 0x91aa067c, 0x8295f72a, 0x732917a6, 0x1d871b4d, 0x4048f136, 0xf1840e7e, 0x6a6048c1,
		0x696cb71a, 0x7ff501c3, 0x0fc6310b, 0x57e0f83d, 0x8cc26e74, 0x11a525a2, 0x946934c7, 0x7cd888f0,
		0x8f9d8604, 0x4f86e73b, 0x04520316, 0xdeeea20c, 0xf1def496, 0x67687288, 0xf540c5b2, 0x22401484,
		0x3478658a, 0xc2385746, 0x01979c2c, 0x5dad73c8, 0x0321f58b, 0xf0fedbee, 0x92826ddf, 0x284bec73,
		0x5b1a1975, 0x03df1e11, 0x20963e01, 0xa17cf12b, 0x740d776e, 0xa7a6bf3c, 0x01b5cce4, 0x1118aa76,
		0xfc6fac0a, 0xce927e9b, 0x00bf2567, 0x806f216c, 0xbca69056, 0x795bd3e9, 0xc9dc4557, 0x8929b6c2,
		0x789d52ec, 0x3f3fbf40, 0xb9197368, 0xa38c15b5, 0xc3b44fa8, 0xca8333b0, 0xb7e8d590, 0xbe807feb,
		0xbf5f8360, 0xd99e2f5c, 0x372928e1, 0x7c757c4c, 0x0db5b154, 0xc01ede02, 0x1fc86e78, 0x1f3985be,
		0xb4805c77, 0x00c880fa, 0x974c1b12, 0x35ab0214, 0xb2dc840d, 0x5b00ae37, 0xd313b026, 0xb260969d,
		0x7f4c8879, 0x1734c4d3, 0x49068631, 0xb9f6a021, 0x6b863e6f, 0xcee5debf, 0x29f8c9fb, 0x53dd6880,
		0x72b61223, 0x1f67a9fd, 0x0a0f6993, 0x13e59119, 0x11cca12e, 0xfe6b6766, 0x16b6effc, 0x97918fc4,
		0xc2b8a563, 0x94f2f741, 0x0bfa8c9a, 0xd1537ae8, 0xc1da349c, 0x873c60ca, 0x95005b85, 0x9b5c080e,
		0xbc8abbd9, 0xe1eab1d2, 0x6dac9070, 0x4ea9ebf1, 0xe0cf30d4, 0x1ef5bd7b, 0xd161043e, 0x5d2fa2e2,
		0xff5d3cae, 0x86ed9f87, 0x2aa1daa1, 0xbd731a34, 0x9e8f4b22, 0xb1c2c67a, 0xc21758c9, 0xa182215d,
		0xccb01948, 0x8d168df7, 0x04238cfe, 0x368c3dbc, 0x0aeadca5, 0xbad21c24, 0x0a71fee5, 0x9fc5d872,
		0x54c152c6, 0xfc329483, 0x6783384a, 0xeddb3e1c, 0x65f90e30, 0x884ad098, 0xce81675a, 0x4b372f7d,
		0x68bf9a39, 0x43445f1e, 0x40f8d8cb, 0x90d5acb6, 0x4cd07282, 0x349eeb06, 0x0c9d5332, 0x520b24ef,
		0x80020447, 0x67976491, 0x2f931ca3, 0xfe9b0535, 0xfcd30220, 0x61a9e6cc, 0xa487d8d7, 0x3f7c5dd1,
		0x7d0127c5, 0x48f51d15, 0x60dea871, 0xc9a91cb7, 0x58b53bb3, 0x9d5e0b2d, 0x624a78b4, 0x30dbee1b,
		0x9bdf22e7, 0x1df5c299, 0x2d5643a7, 0xf4dd35ff, 0x03ca8fd6, 0x53b47ed8, 0x6f2c19aa, 0xfeb0c1f4,
		0x49e54438, 0x2f2577e6, 0xbf876969, 0x72440ea9, 0xfa0bafb8, 0x74f5b3a0, 0x7dd357cd, 0x89ce1358,
		0x6ef2cdda, 0x1e7767f3, 0xa6be9fdb, 0x4f5f88f8, 0xba994a3a, 0x08ca6b65, 0xe0893818, 0x9e00a16a,
		0xf42bfc8f, 0x9972eedc, 0x749c8b51, 0x32c05f5e, 0xd706805f, 0x6bfbb7cf, 0xd9210a10, 0x31a1db97,
		0x923a9559, 0x37a7a1f6, 0x059f8861, 0xca493e62, 0x65157e81, 0x8f6467dd, 0xab85ff9f, 0x9331aff2,
		0x8616b9f5, 0xedbd5695, 0xee7e29b1, 0x313ac44f, 0xb903112f, 0x432ef649, 0xdc0a36c0, 0x61cf2bba,
		0x81474925, 0xa8b6c7ad, 0xee5931de, 0xb2f8158d, 0x59fb7409, 0x2e3dfaed, 0x9af25a3f, 0xe1fed4d5
	]),

	besttrigtab: [
		[550, 900, 800, 700, 500, 350, 300, 200, 180, 180, 160],
		[110, 550, 900, 800, 550, 400, 350, 250, 140, 160, 140],
		[100, 120, 550, 900, 700, 500, 400, 300, 220, 250, 160]
	],

	lzeroes: new Int32Array([
		8, 7, 6, 6, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3, 3,
		2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
		1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
		1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
		0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
	]),

	J: new Int32Array([
		0, 0, 0, 0, 1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 5, 5, 6, 6, 7,
		7, 8, 9, 10, 11, 12, 13, 14, 15
	]),

	zeroLUT: null,

	BPC_MASK: {
		4: 0xff,
		5: 0xff,
		24: 0xff,
		16: 0x1f
	},

	stabrand: function() {
		return this.TABRAND_SEEDMASK;
	},

	tabrand: function(rgb_state) {
		rgb_state.tabrand_seed++;
		return this.tabrand_chaos[rgb_state.tabrand_seed & this.TABRAND_SEEDMASK];
	},

	set_wm_trigger: function(state) {
		var wm = state.wmidx;
		if (wm > 10) {
			wm = 10;
		}

		//>> 1 == / 2
		state.wm_trigger = wdi.JSQuic.besttrigtab[Math.floor(wdi.JSQuic.evol >> 1)][wm];
	},

	ceil_log_2: function(val) {
		var result;

		if (val === 1) {
			return 0;
		}

		result = 1;
		val -= 1;
		while ((val >>>= 1)) {
			result++;
		}

		return result;
	},

	decorelate_init: function(family, bpc) {
		var pixelbitmask = this.bppmask[bpc];
		var pixelbitmaskshr = pixelbitmask >>> 1;
		var s;

		for (s = 0; s <= pixelbitmask; s++) {
			if (s <= pixelbitmaskshr) {
				family.xlatU2L[s] = (s << 1) >>> 0;
			} else {
				family.xlatU2L[s] = (((pixelbitmask - s) << 1) >>> 0) + 1;
			}
		}
	},

	corelate_init: function(family, bpc) {
		var pixelbitmask = this.bppmask[bpc];
		var s;

		for (s = 0; s <= pixelbitmask; s++) {
			if (s & 0x01) {
				family.xlatL2U[s] = pixelbitmask - (s >>> 1);
			} else {
				family.xlatL2U[s] = (s >>> 1);
			}
		}
	},

	family_init: function(family, bpc, limit) {
		var l;

		for (l = 0; l < bpc; l++) {
			var altprefixlen, altcodewords;

			altprefixlen = limit - bpc;
			if (altprefixlen > parseInt(this.bppmask[bpc - l])) {
				altprefixlen = this.bppmask[bpc - l];
			}

			altcodewords = this.bppmask[bpc] + 1 - ((altprefixlen << l) >>> 0);

			family.nGRcodewords[l] = ((altprefixlen << l) >>> 0);
			family.notGRcwlen[l] = altprefixlen + this.ceil_log_2(altcodewords);
			family.notGRprefixmask[l] = this.bppmask[32 - altprefixlen];
			family.notGRsuffixlen[l] = this.ceil_log_2(altcodewords);
		}

		//this.decorelate_init(family, bpc);
		this.corelate_init(family, bpc);
	},

	init_zeroLUT: function() {

		this.zeroLUT = new Int32Array(256);

		var i, j, k, l;

		j = k = 1;
		l = 8;
		for (i = 0; i < 256; ++i) {
			this.zeroLUT[i] = l;
			--k;
			if (k === 0) {
				k = j;
				--l;
				j *= 2;
			}
		}
	},

	quic_init: function() {
		this.family_init(this.family_8bpc, 8, this.DEFmaxclen);
		//this.family_init(this.family_5bpc, 5, this.DEFmaxclen);
		this.init_zeroLUT();

		//perf improvment
		wdi.xlatL2U = new Int32Array(this.family_8bpc.xlatL2U.length);
		wdi.xlatL2U.set(this.family_8bpc.xlatL2U);

		wdi.notGRprefixmask = new Int32Array(this.family_8bpc.notGRprefixmask.length);
		wdi.notGRprefixmask.set(this.family_8bpc.notGRprefixmask);

		wdi.nGRcodewords = new Int32Array(this.family_8bpc.nGRcodewords.length);
		wdi.nGRcodewords.set(this.family_8bpc.nGRcodewords);


		wdi.notGRcwlen = new Int32Array(this.family_8bpc.notGRcwlen.length);
		wdi.notGRcwlen.set(this.family_8bpc.notGRcwlen);

		wdi.notGRsuffixlen = new Int32Array(this.family_8bpc.notGRsuffixlen.length);
		wdi.notGRsuffixlen.set(this.family_8bpc.notGRsuffixlen);


		//prepare precomputed lzeroes tables
		var lzeroes = wdi.JSQuic.lzeroes;
		var lzeroes8 = new Int32Array(lzeroes);
		var len = lzeroes.length;
		for (var i = 0; i < len; i++) {
			lzeroes8[i] = lzeroes[i] + 8;
		}
		wdi.JSQuic.lzeroes8 = lzeroes8;

		//prepare precomputed lzeroes tables
		var lzeroes16 = new Int32Array(lzeroes);
		for (var i = 0; i < len; i++) {
			lzeroes16[i] = lzeroes[i] + 16;
		}
		wdi.JSQuic.lzeroes16 = lzeroes16;

		//prepare precomputed lzeroes tables
		var lzeroes24 = new Int32Array(lzeroes);
		for (var i = 0; i < len; i++) {
			lzeroes24[i] = lzeroes[i] + 24;
		}
		wdi.JSQuic.lzeroes24 = lzeroes24;
	},

	quic_image_params: function(encoder, type) {
		var channels, bpc;
		switch (type) {
			case wdi.QuicImageType.QUIC_IMAGE_TYPE_GRAY:
				channels = 1;
				bpc = 8;
				break;
			case wdi.QuicImageType.QUIC_IMAGE_TYPE_RGB16:
				channels = 3;
				bpc = 5;
				break;
			case wdi.QuicImageType.QUIC_IMAGE_TYPE_RGB24:
				channels = 3;
				bpc = 8;
				break;
			case wdi.QuicImageType.QUIC_IMAGE_TYPE_RGB32:
				channels = 3;
				bpc = 8;
				break;
			case wdi.QuicImageType.QUIC_IMAGE_TYPE_RGBA:
				channels = 4;
				bpc = 8;
				break;
			case wdi.QuicImageType.QUIC_IMAGE_TYPE_INVALID:
			default:
				channels = 0;
				bpc = 0;
		}
		return [channels, bpc];
	},

	find_model_params: function(encoder, bpc) {
		var bsize = 0;
		var bstart = 0;
		var bend = 0;
		var repcntr = 0;

		var result = {};

		result.ncounters = 8;

		result.levels = 0x1 << bpc;

		result.n_buckets_ptrs = 0;

		switch (this.evol) {
			case 1:
				result.repfirst = 3;
				result.firstsize = 1;
				result.repnext = 2;
				result.mulsize = 2;
				break;
			case 3:
				result.repfirst = 1;
				result.firstsize = 1;
				result.repnext = 1;
				result.mulsize = 2;
				break;
			case 5:
				result.repfirst = 1;
				result.firstsize = 1;
				result.repnext = 1;
				result.mulsize = 4;
				break;
			case 0:
			case 2:
			case 4:
			default:
				wdi.Debug.error('fund model params: invalid evol');
				return false;
		}

		result.nbuckets = 0;
		repcntr = result.repfirst + 1;
		bsize = result.firstsize;

		do { /* other buckets */
			if (result.nbuckets) {
				bstart = bend + 1;
			} else {
				bstart = 0;
			}

			if (!--repcntr) {
				repcntr = result.repnext;
				bsize *= result.mulsize;
			}

			bend = bstart + bsize - 1;
			if (bend + bsize >= result.levels) {
				bend = result.levels - 1;
			}

			if (!result.n_buckets_ptrs) {
				result.n_buckets_ptrs = result.levels;
			}

			result.nbuckets++;
		} while (bend < result.levels - 1);
		return result;
	},

	init_model_structures: function(encoder, family, params) {
		family.buckets_buf = [];
		for (var i = 0; i < params.nbuckets; i++) {
			family.buckets_buf[i] = new wdi_quic_s_bucket();
		}
		family.buckets_ptrs = [];
		family.counters = [];
		this.fill_model_structures(encoder, family, params);
	},

	fill_model_structures: function(encoder, family, params) {
		var bsize, bstart, bend = 0,
			repcntr, bnumber;

		bnumber = 0;

		repcntr = params.repfirst + 1;
		bsize = params.firstsize;


		do {
			if (bnumber) {
				bstart = bend + 1;
			} else {
				bstart = 0;
			}

			if (!--repcntr) {
				repcntr = params.repnext;
				bsize *= params.mulsize;
			}

			bend = bstart + bsize - 1;
			if (bend + bsize >= params.levels) {
				bend = params.levels - 1;
			}

			family.buckets_buf[bnumber].pcounters = new Int32Array(params.ncounters);
			for (var x = 0; x < params.ncounters; x++) {
				family.buckets_buf[bnumber].pcounters[x] = 0;
			}

			for (var i = bstart; i <= bend; i++) {
				family.buckets_ptrs[i] = family.buckets_buf[bnumber];
			}


			bnumber++;
		} while (bend < params.levels - 1);
	},

	initChannel: function(encoder, channel) {
		channel.encoder = encoder;
		channel.state.encoder = encoder;
		channel.correlate_row_width = 0;
		channel.correlate_row = null;

		var params = this.find_model_params(encoder, 8);
		encoder.n_buckets_8bpc = params.nbuckets;
		this.init_model_structures(encoder, channel.family_stat_8bpc, params);

		params = this.find_model_params(encoder, 5);
		encoder.n_buckets_5bpc = params.nbuckets;
		this.init_model_structures(encoder, channel.family_stat_5bpc, params);
	},

	encoder_reste_channels: function(encoder, channels, width, bpc) {
		encoder.num_channels = channels;
		for (var i = 0; i < channels; i++) {
			var bucket, end_bucket;

			if (encoder.channels[i].correlate_row_width < width) {
				encoder.channels[i].correlate_row = new Array(width);
				encoder.channels[i].correlate_row_width = width;
			}
			encoder.channels[i].num_channel = i;
			if (bpc === 8) {
				bucket = encoder.channels[i].family_stat_8bpc.buckets_buf;
				end_bucket = encoder.n_buckets_8bpc;
				for (var x = 0; x < end_bucket; x++) {
					bucket[x].bestcode = 8 - 1;
				}
				encoder.channels[i]._buckets_ptrs = encoder.channels[i].family_stat_8bpc.buckets_ptrs;
			} else if (bpc === 5) {
				bucket = encoder.channels[i].family_stat_5bpc.buckets_buf;
				end_bucket = encoder.n_buckets_5bpc;
				for (var x = 0; x < end_bucket; x++) {
					bucket[x].bestcode = /*BPC*/ 5 - 1;
				}
				encoder.channels[i]._buckets_ptrs = encoder.channels[i].family_stat_5bpc.buckets_ptrs;
			} else {
				return FALSE;
			}

			encoder.channels[i].state.waitcnt = 0;
			encoder.channels[i].state.tabrand_seed = wdi.JSQuic.stabrand();
			encoder.channels[i].state.wmidx = wdi.JSQuic.DEFwmistart;
			encoder.channels[i].state.wmileft = wdi.JSQuic.wminext;
		}
		return true;
	},

	decode_channel_run: function(encoder, channel) {
		var runlen = 0;

		do {
			var temp, hits;
			//TODO: casting needed?
			temp = wdi.JSQuic.zeroLUT[(~(encoder.io_word >>> 24) >>> 0) % 256];

			for (hits = 1; hits <= temp; hits++) {
				runlen += channel.state.melcorder;

				if (channel.state.melcstate < 32) {
					channel.state.melclen = wdi.JSQuic.J[++channel.state.melcstate];
					channel.state.melcorder = (1 << channel.state.melclen) >>> 0;
				}
			}
			if (temp !== 8) {
				encoder.eatbits(temp + 1, encoder);
				break;
			}
			encoder.eatbits(8, encoder);
		} while (1);

		/* read the length of the remainder */
		if (channel.state.melclen) {
			runlen += encoder.io_word >>> (32 - channel.state.melclen);
			encoder.eatbits(channel.state.melclen, encoder);
		}

		/* adjust melcoder parameters */
		if (channel.state.melcstate) {
			channel.state.melclen = wdi.JSQuic.J[--channel.state.melcstate];
			channel.state.melcorder = (1 << channel.state.melclen) >>> 0;
		}

		return runlen;
	},

	decode_run: function(encoder) {
		var runlen = 0;
		var temp, hits, tempadd;
		var zeroLUT = wdi.JSQuic.zeroLUT;
		var rgb_state = encoder.rgb_state;
		var J = wdi.JSQuic.J;
		var eatbits = encoder.eatbits;
		do {

			//TODO: casting needed?
			temp = zeroLUT[(~(encoder.io_word >>> 24) >>> 0) % 256];
			tempadd = temp + 1;
			for (hits = 1; hits < tempadd; hits++) {
				runlen += encoder.rgb_state.melcorder;

				if (rgb_state.melcstate < 32) {
					rgb_state.melclen = J[++rgb_state.melcstate];
					rgb_state.melcorder = (1 << rgb_state.melclen) >>> 0;
				}
			}
			if (temp !== 8) {
				eatbits(tempadd, encoder);
				break;
			}
			encoder.eatbits(8, encoder);
		} while (1);

		if (rgb_state.melclen) {
			runlen += encoder.io_word >>> (32 - rgb_state.melclen);
			eatbits(rgb_state.melclen, encoder);
		}

		if (rgb_state.melcstate) {
			rgb_state.melclen = J[--rgb_state.melcstate];
			rgb_state.melcorder = (1 << rgb_state.melclen) >>> 0;
		}

		return runlen;
	},

	quic_decode: function(data) {
		//console.time("test");
		var view = new Uint32Array(data);
		var encoder = new wdi_quic_Encoder(view);
		var opaque = encoder.io_word & 0x0000FF00;
		var format = (encoder.io_word >>> 24) & 0xFF;


		encoder.eat32bits(); //skip quic size

		encoder.eat32bits();
		var magic = encoder.io_word;
		encoder.eat32bits();

		var version = encoder.io_word;
		encoder.eat32bits();

		var type = encoder.io_word;
		encoder.eat32bits();

		encoder.type = type; //here?

		var width = encoder.io_word;
		encoder.width = width; //here?
		encoder.eat32bits();

		var height = encoder.io_word;
		encoder.height = height; //here?
		encoder.eat32bits();

		var result = wdi.JSQuic.quic_image_params(encoder, type);
		var channels = result[0];
		var bpc = result[1];

		this.encoder_reste_channels(encoder, channels, width, bpc);

		var buf = new ArrayBuffer(width * height * 4);
		var buf8 = new Uint8Array(buf);
		var data = new Uint32Array(buf);
		encoder.result = buf8;
		encoder.resultData = data;
		encoder.setComputedWidth(width);

		switch (type) {
			case wdi.QuicImageType.QUIC_IMAGE_TYPE_RGB32:
			case wdi.QuicImageType.QUIC_IMAGE_TYPE_RGB24:
				//ASSERT(encoder->usr, ABS(stride) >= (int)encoder->width * 4);
				QUIC_UNCOMPRESS_RGB(encoder, channels, bpc, type);
				break;
			case wdi.QuicImageType.QUIC_IMAGE_TYPE_RGB16:
				//				if (type == QUIC_IMAGE_TYPE_RGB16) {
				//					//ASSERT(encoder->usr, ABS(stride) >= (int)encoder->width * 2);
				//					QUIC_UNCOMPRESS_RGB(16, rgb16_pixel_t);
				//				} else if (type == QUIC_IMAGE_TYPE_RGB32) {
				//					//ASSERT(encoder->usr, ABS(stride) >= (int)encoder->width * 4);
				//					QUIC_UNCOMPRESS_RGB(16_to_32, rgb32_pixel_t);
				//				} else {
				//					//encoder->usr->warn(encoder->usr, "unsupported output format\n");
				//					return QUIC_ERROR;
				//				}

				break;
			case wdi.QuicImageType.QUIC_IMAGE_TYPE_RGBA:
				QUIC_UNCOMPRESS_RGBA(encoder, channels, bpc, type);
				if (opaque) {
					var len = buf8.length - 1;
					while (len > 0) {
						buf8[len] = 255;
						len -= 4;
					}
				}
				break;
			//QUIC_UNCOMPRESS_RGBA(encoder, channels, bpc, type);
			//
			//				if (type != QUIC_IMAGE_TYPE_RGBA) {
			//					//encoder->usr->warn(encoder->usr, "unsupported output format\n");
			//					return QUIC_ERROR;
			//				}
			//				//ASSERT(encoder->usr, ABS(stride) >= (int)encoder->width * 4);
			//				uncompress_rgba(encoder, buf, stride);
			//				break;
		}
		//		var len = encoder.result.length;
		//		while(len--) {
		//			imgData.data[len] = encoder.result[len];
		//		}
		//console.timeEnd("test");

		//imgData.data.set(buf8);
		return buf;
	}

};

wdi.JSQuic.quic_init();

function wdi_quic_Encoder(data) {
	this.computedWidth = 0;
	this.result = [];
	this.cnt = 0;
	this.pxCnt = 0,
		this.usr = data;
	this.type = null;
	this.width = null;
	this.height = null;
	this.num_channels = null;

	this.n_buckets_8bpc = null;
	this.n_buckets_5bpc = null;

	this.io_available_bits = 32;
	this.io_now = 0;

	this.io_next_word = null;
	this.io_now = null;

	this.read_io_word();
	this.io_word = this.io_next_word;

	this.read_io_word();

	this.io_words_count = data.length;

	this.rows_completed = 0; //??

	this.channels = [];

	this.alphaPos = 3; //first alpha

	this.rgb_state = new wdi_quic_CommonState();
	for (var i = 0; i < 4; i++) {
		this.channels[i] = new wdi_quic_Channel();
		wdi.JSQuic.initChannel(this, this.channels[i]);
	}
}

wdi_quic_Encoder.prototype.append = function(databyte) {
	this.result[this.cnt++] = databyte;
}

wdi_quic_Encoder.prototype.appendPixel = function(r, g, b) {
	this.resultData[this.pxCnt++] =
		(255 << 24) | // alpha
		(b << 16) | // blue
		(g << 8) | // green
		r; // red
	this.cnt += 4;
}

wdi_quic_Encoder.prototype.eatbits = function(len, encoder) {
	var available_bits = encoder.io_available_bits;
	var io_word = encoder.io_word;

	var delta = available_bits - len;

	io_word = io_word << len;

	//enough bits
	if (delta >= 0) {
		io_word = (io_word | encoder.io_next_word >>> delta) >>> 0;
		encoder.io_available_bits = delta;
		encoder.io_word = io_word;
		return;
	}

	var io_next_word = encoder.io_next_word;
	//not enough bits
	delta = -delta; //bits missing
	io_word = (io_word | (io_next_word << delta) >>> 0);

	///////////////////
	//read io word (inlined for perforemance)

	io_next_word = encoder.usr[encoder.io_now++];
	//end read io_word
	/////////////////

	available_bits = 32 - delta;
	io_word = (io_word | (io_next_word >>> available_bits)) >>> 0;

	encoder.io_available_bits = available_bits;
	encoder.io_word = io_word;
	encoder.io_next_word = io_next_word;
}

wdi_quic_Encoder.prototype.eat32bits = function() {
	this.eatbits(16, this);
	this.eatbits(16, this);
}

wdi_quic_Encoder.prototype.read_io_word = function() {
	this.io_next_word = this.usr[this.io_now++];
}

wdi_quic_Encoder.prototype.row_completed = function() {
	this.rows_completed++;
}

wdi_quic_Encoder.prototype.setComputedWidth = function(width) {
	this.computedWidth = width * 4;
}

wdi_quic_Encoder.prototype.appendAlpha = function(databyte) {
	this.result[this.alphaPos] = databyte;
	this.alphaPos += 4;
}

function cnt_l_zeroes(bits) {
	if (bits > 0x007FFFFF) {
		return wdi.JSQuic.lzeroes[bits >>> 24];
	} else if (bits > 0x00007FFF) {
		return 8 + wdi.JSQuic.lzeroes[((bits >>> 16) & 0x000000ff)];
	} else if (bits > 0x0000007F) {
		return 16 + wdi.JSQuic.lzeroes[((bits >>> 8) & 0x000000ff)];
	} else {
		return 24 + wdi.JSQuic.lzeroes[(bits & 0x000000ff)];
	}
}


/*
 *
 *
 * JSQUIC FAMILY
 *
 *
 */

function golomb_code_len(n, l) {
	if (n < wdi.nGRcodewords[l]) {
		return (n >>> l) + 1 + l;
	} else {
		return wdi.notGRcwlen[l];
	}
}

function golomb_decoding(l, bits, bppmask, notGRprefixmask, notGRcwlen, nGRcodewords, notGRsuffixlen) {
	var cwlen;
	var result;
	//its better to check first for bigger, tested for performance
	if (bits > notGRprefixmask[l]) {
		var zeroprefix = cnt_l_zeroes(bits);
		cwlen = zeroprefix + 1 + l;
		result = ((zeroprefix << l)) | ((bits >>> (32 - cwlen)) & bppmask[l]);
	} else {
		cwlen = notGRcwlen[l];
		result = nGRcodewords[l] + ((bits) >>> (32 - cwlen) & bppmask[notGRsuffixlen[l]]);
	}
	return [result, cwlen];
}

/* update the bucket using just encoded curval */
function real_update_model(state, bucket, curval, bpp, wm_trigger) {
	var i;
	var bestcode;
	var bestcodelen;
	var ithcodelen;

	var pcounters = bucket.pcounters;
	bestcode = bpp - 1;
	bestcodelen = (pcounters[bestcode] += golomb_code_len(curval, bestcode));

	for (i = bpp - 2; i >= 0; i--) {
		ithcodelen = (pcounters[i] += golomb_code_len(curval, i));

		if (ithcodelen < bestcodelen) {
			bestcode = i;
			bestcodelen = ithcodelen;
		}
	}

	bucket.bestcode = bestcode;
	if (bestcodelen > state.wm_trigger) {
		while (bpp-- > 0) {
			pcounters[bpp] >>>= 1;
		}
	}
}

function UPDATE_MODEL(index, encoder, bpp, correlate_row_r, correlate_row_g, correlate_row_b) {
	real_update_model(encoder.rgb_state, find_bucket(encoder.channels[0],
		correlate_row_r[index - 1]), correlate_row_r[index], bpp);
	real_update_model(encoder.rgb_state, find_bucket(encoder.channels[1],
		correlate_row_g[index - 1]), correlate_row_g[index], bpp);
	real_update_model(encoder.rgb_state, find_bucket(encoder.channels[2],
		correlate_row_b[index - 1]), correlate_row_b[index], bpp);
}

function find_bucket(channel, val) {
	if (val === undefined) {
		val = channel.oldFirst;
	}
	return channel._buckets_ptrs[val];
}

/*
 *
 *
 * JSQUIC RGBA
 *
 *
 */

function QUIC_UNCOMPRESS_RGBA(encoder, channels, bpc, type) {
	quic_uncompress_row0(encoder, channels, bpc, type);
	quic_four_uncompress_row0(encoder, encoder.channels[3], bpc, type);
	encoder.row_completed();
	var height = encoder.height;
	var rgb_state = encoder.rgb_state;
	for (var row = 1; row < height; row++) {
		quic_uncompress_row_a(encoder, channels, bpc, type, rgb_state);
		quic_four_uncompress_row(encoder, encoder.channels[3], bpc, type);
		encoder.row_completed();
	}
}

function quic_four_uncompress_row(encoder, channel, bpc, type) {
	var bpc_mask = wdi.JSQuic.BPC_MASK[type];
	var pos = 0;
	var width = encoder.width;
	while ((wdi.JSQuic.wmimax > channel.state.wmidx) && (channel.state.wmileft <= width)) {
		if (channel.state.wmileft) {
			uncompress_four_row_seg(
				encoder,
				channel,
				pos,
				pos + channel.state.wmileft,
				bpc,
				bpc_mask,
				type
			);
			pos += channel.state.wmileft;
			width -= channel.state.wmileft;
		}

		channel.state.wmidx++;
		wdi.JSQuic.set_wm_trigger(channel.state);
		channel.state.wmileft = wdi.JSQuic.wminext;
	}

	if (width) {
		uncompress_four_row_seg(
			encoder,
			channel,
			pos,
			pos + width,
			bpc,
			bpc_mask,
			type
		);
		if (wdi.JSQuic.wmimax > channel.state.wmidx) {
			channel.state.wmileft -= width;
		}
	}
}

function uncompress_four_row_seg(encoder, channel, i, end, bpc, bpc_mask, type) {
	var correlate_row = channel.correlate_row;

	var stopidx = 0;

	var waitmask = wdi.JSQuic.bppmask[channel.state.wmidx];

	var run_index = 0;
	var run_end = 0;

	var rle = false;

	var computedWidth = encoder.computedWidth;

	var rows_completed = encoder.rows_completed;

	var offset = ((encoder.rows_completed - 1) * computedWidth);

	var data;

	var eatbits = encoder.eatbits;
	var appendAlpha = encoder.appendAlpha;

	var alpha;

	var ret, codewordlen;
	var bppmask = wdi.JSQuic.bppmask;

	var notGRprefixmask = wdi.notGRprefixmask;
	var notGRcwlen = wdi.notGRcwlen;
	var nGRcodewords = wdi.nGRcodewords;
	var notGRsuffixlen = wdi.notGRsuffixlen;

	if (!i) {
		alpha = UNCOMPRESS_ONE_0_A(channel, encoder, bpc_mask, offset);

		if (channel.state.waitcnt) {
			--channel.state.waitcnt;
		} else {
			channel.state.waitcnt = (wdi.JSQuic.tabrand(channel.state) & waitmask);
			real_update_model(channel.state, find_bucket(channel,
				correlate_row[-1]), correlate_row[0], bpc);
		}
		stopidx = ++i + channel.state.waitcnt;
	} else {
		stopidx = i + channel.state.waitcnt;
		alpha = encoder.result[encoder.alphaPos - 4];
	}

	for (;;) {
		while (stopidx < end) {
			for (; i <= stopidx; i++) {
				rle = RLE_PRED_A(i, encoder, run_index, computedWidth, rows_completed);
				if (rle) break;

				ret = golomb_decoding(find_bucket(channel, correlate_row[i - 1]).bestcode,
					encoder.io_word, bppmask, notGRprefixmask, notGRcwlen, nGRcodewords, notGRsuffixlen);

				data = ret[0];
				codewordlen = ret[1];

				correlate_row[i] = data;
				alpha = (((wdi.xlatL2U[data] +
				((alpha + PIXEL_B(channel, encoder, i, offset)) >>> 1)) & bpc_mask) >>> 0);

				appendAlpha.call(encoder, alpha);
				eatbits(codewordlen, encoder);
			}
			if (!rle) {
				real_update_model(channel.state, find_bucket(channel,
					correlate_row[stopidx - 1]), correlate_row[stopidx], bpc);
				stopidx = i + (wdi.JSQuic.tabrand(channel.state) & waitmask);
			} else {
				break;
			}
		}
		if (!rle) {
			for (; i < end; i++) {
				rle = RLE_PRED_A(i, encoder, run_index, computedWidth, rows_completed);
				if (rle) break;

				ret = golomb_decoding(find_bucket(channel, correlate_row[i - 1]).bestcode,
					encoder.io_word, bppmask, notGRprefixmask, notGRcwlen, nGRcodewords, notGRsuffixlen);

				data = ret[0];
				codewordlen = ret[1];
				correlate_row[i] = data;
				alpha = (((wdi.xlatL2U[data] +
				((alpha + PIXEL_B(channel, encoder, i, offset)) >>> 1)) & bpc_mask) >>> 0);

				appendAlpha.call(encoder, alpha);
				eatbits(codewordlen, encoder);
			}
			if (!rle) {
				channel.state.waitcnt = stopidx - end;
				return;
			}
		}

		//RLE
		channel.state.waitcnt = stopidx - i;
		run_index = i;
		run_end = i + wdi.JSQuic.decode_channel_run(encoder, channel);

		var cpos = ((encoder.rows_completed) * (encoder.width * 4)) + (i * 4);
		var a = encoder.result[cpos - 1];

		for (; i < run_end; i++) {
			//TODO: how to append?
			appendAlpha.call(encoder, a);
		}

		if (i === end) {
			return;
		}

		stopidx = i + channel.state.waitcnt;
		rle = false;
		//END RLE
	}
}


function quic_four_uncompress_row0(encoder, channel, bpc, type) {
	var bpc_mask = wdi.JSQuic.BPC_MASK[type];
	var pos = 0;
	var width = encoder.width;
	while ((wdi.JSQuic.wmimax > channel.state.wmidx) && (channel.state.wmileft <= width)) {
		if (channel.state.wmileft) {
			uncompress_four_row0_seg(
				encoder,
				channel,
				pos,
				pos + channel.wmileft,
				wdi.JSQuic.bppmask[channel.state.wmidx],
				bpc,
				bpc_mask,
				type
			);
			pos += channel.state.wmileft;
			width -= channel.state.wmileft;
		}

		channel.state.wmidx++;
		wdi.JSQuic.set_wm_trigger(channel.state);
		channel.state.wmileft = wdi.JSQuic.wminext;
	}

	if (width) {
		uncompress_four_row0_seg(
			encoder,
			channel,
			pos,
			pos + width,
			wdi.JSQuic.bppmask[channel.state.wmidx],
			bpc,
			bpc_mask,
			type
		);
		if (wdi.JSQuic.wmimax > channel.state.wmidx) {
			channel.state.wmileft -= width;
		}
	}
}

function uncompress_four_row0_seg(encoder, channel, i, end, waitmask, bpc, bpc_mask, type) {
	var correlate_row = channel.correlate_row;

	var stopidx = 0;

	if (!i) {
		UNCOMPRESS_ONE_ROW0_0_A(channel);

		if (channel.state.waitcnt) {
			--channel.state.waitcnt;
		} else {
			channel.state.waitcnt = (wdi.JSQuic.tabrand(channel.state) & waitmask);
			real_update_model(channel.state, find_bucket(channel,
				correlate_row[-1]), correlate_row[0], bpc);
		}
		stopidx = ++i + channel.state.waitcnt;
	} else {
		stopidx = i + channel.state.waitcnt;
	}

	while (stopidx < end) {
		for (; i <= stopidx; i++) {
			UNCOMPRESS_ONE_ROW0_A(channel, i, bpc_mask, encoder, correlate_row);
		}
		real_update_model(channel.state, find_bucket(channel,
			correlate_row[stopidx - 1]), correlate_row[stopidx], bpc);
		stopidx = i + (wdi.JSQuic.tabrand(channel.state) & waitmask);
	}

	for (; i < end; i++) {
		UNCOMPRESS_ONE_ROW0_A(channel, i, bpc_mask, encoder, correlate_row);
	}
	channel.state.waitcnt = stopidx - end;
}

function SAME_PIXEL_A(i, result) {
	if (result[i - 1] === result[i + 3]) {
		return true;
	}
	return false;
}

function RLE_PRED_A(i, encoder, run_index, width, rows_completed) {
	var pr = ((rows_completed - 1) * width) + (i * 4); //prev r
	if (run_index !== i && i > 2) {
		if (SAME_PIXEL_A(pr, encoder.result)) {
			pr = ((rows_completed) * width) + ((i - 1) * 4); // cur r
			if (SAME_PIXEL_A(pr, encoder.result)) {
				return true;
			}
		}
	}
	return false;
}

function UNCOMPRESS_ONE_0_A(channel, encoder, bpc_mask, offset) {
	var ret, codewordlen;
	channel.oldFirst = channel.correlate_row[0];
	ret = golomb_decoding(find_bucket(channel,
		channel.correlate_row[-1]).bestcode, encoder.io_word, wdi.JSQuic.bppmask, wdi.notGRprefixmask, wdi.notGRcwlen, wdi.nGRcodewords, wdi.notGRsuffixlen);
	channel.correlate_row[0] = ret[0];
	codewordlen = ret[1];
	var residuum = wdi.xlatL2U[channel.correlate_row[0]];
	var prev = PIXEL_B(channel, encoder, 0, offset);
	var resultpixel = ((residuum + prev) & bpc_mask) >>> 0;
	encoder.appendAlpha(resultpixel);
	encoder.eatbits(codewordlen, encoder);
	return resultpixel;
}

function UNCOMPRESS_ONE_A(channel, i, bpc_mask, encoder, correlate_row, offset) {
	var ret, codewordlen;
	ret = golomb_decoding(find_bucket(channel, correlate_row[i - 1]).bestcode,
		encoder.io_word, wdi.JSQuic.bppmask, wdi.notGRprefixmask, wdi.notGRcwlen, wdi.nGRcodewords, wdi.notGRsuffixlen);
	var data = ret[0];
	codewordlen = ret[1];
	correlate_row[i] = data;
	encoder.appendAlpha((((wdi.xlatL2U[data] +
	((PIXEL_A_A(encoder) + PIXEL_B(channel, encoder, i, offset)) >>> 1)) & bpc_mask) >>> 0));

	encoder.eatbits(codewordlen, encoder);
}


function UNCOMPRESS_ONE_ROW0_0_A(channel) {
	var ret, codewordlen;
	var encoder = channel.encoder;
	ret = golomb_decoding(find_bucket(channel, 0).bestcode, encoder.io_word, wdi.JSQuic.bppmask, wdi.notGRprefixmask, wdi.notGRcwlen, wdi.nGRcodewords, wdi.notGRsuffixlen);
	channel.correlate_row[0] = ret[0];
	codewordlen = ret[1];
	encoder.appendAlpha(wdi.xlatL2U[channel.correlate_row[0]]);
	encoder.eatbits(codewordlen, encoder);
}

function UNCOMPRESS_ONE_ROW0_A(channel, i, bpc_mask, encoder, correlate_row) {
	var ret, codewordlen;
	ret = golomb_decoding(find_bucket(channel, correlate_row[i - 1]).bestcode, encoder.io_word, wdi.JSQuic.bppmask, wdi.notGRprefixmask, wdi.notGRcwlen, wdi.nGRcodewords, wdi.notGRsuffixlen);
	var data = ret[0];
	codewordlen = ret[1];
	correlate_row[i] = data;
	encoder.appendAlpha(CORELATE_0_A(encoder, channel, i, bpc_mask, correlate_row));
	encoder.eatbits(codewordlen, encoder);
}

function CORELATE_0_A(encoder, channel, curr, bpc_mask, correlate_row) {
	return ((wdi.xlatL2U[correlate_row[curr]] + PIXEL_A_A(encoder)) & bpc_mask) >>> 0;
}

function PIXEL_A_A(encoder) {
	return encoder.result[encoder.alphaPos - 4];
}

/*
 *
 *
 * JSQUIC UNCOMPRESS
 *
 *
 */

function QUIC_UNCOMPRESS_RGB(encoder, channels, bpc, type) {
	quic_uncompress_row0(encoder, channels, bpc, type);
	encoder.row_completed();

	var rgb_state = encoder.rgb_state;
	var height = encoder.height;
	var computedAlpha = 255 << 24;
	var result = encoder.result;
	var resultData = encoder.resultData;
	var width = encoder.width;
	var bpc_mask = wdi.JSQuic.BPC_MASK[type];
	var jsquic = wdi.JSQuic;
	var channel_r = encoder.channels[0];
	var channel_g = encoder.channels[1];
	var channel_b = encoder.channels[2];
	var buckets_ptrs_r = channel_r._buckets_ptrs;
	var buckets_ptrs_g = channel_g._buckets_ptrs;
	var buckets_ptrs_b = channel_b._buckets_ptrs;
	var correlate_row_r = channel_r.correlate_row;
	var correlate_row_g = channel_g.correlate_row;
	var correlate_row_b = channel_b.correlate_row;
	var computedWidth = encoder.computedWidth;
	var xlatL2U = wdi.xlatL2U;
	var lzeroes = wdi.JSQuic.lzeroes;
	var lzeroes8 = wdi.JSQuic.lzeroes8;
	var lzeroes16 = wdi.JSQuic.lzeroes16;
	var lzeroes24 = wdi.JSQuic.lzeroes24;
	var notGRprefixmask = wdi.notGRprefixmask;
	var notGRcwlen = wdi.notGRcwlen;
	var nGRcodewords = wdi.nGRcodewords;
	var notGRsuffixlen = wdi.notGRsuffixlen;
	var eatbits = encoder.eatbits;
	var tabrand = wdi.JSQuic.tabrand;
	var decode_run = wdi.JSQuic.decode_run;
	var bppmask = wdi.JSQuic.bppmask;
	var jsquic = wdi.JSQuic;
	var tabrand_chaos = wdi.JSQuic.tabrand_chaos;
	var tabrand_seedmask = jsquic.TABRAND_SEEDMASK;
	var usr = encoder.usr;

	for (var row = 1; row < height; row++) {
		quic_uncompress_row(encoder, channels, bpc, type, rgb_state, computedAlpha, result, resultData, width, bpc_mask,
			jsquic, channel_r, channel_g, channel_b, buckets_ptrs_r, buckets_ptrs_g, buckets_ptrs_b, correlate_row_r,
			correlate_row_g, correlate_row_b, computedWidth, xlatL2U, lzeroes, lzeroes8, lzeroes16, lzeroes24,
			notGRprefixmask, notGRcwlen, nGRcodewords, notGRsuffixlen, eatbits, tabrand, decode_run, bppmask, tabrand_chaos,
			tabrand_seedmask, usr);
		encoder.rows_completed++;
	}
}


function quic_uncompress_row(encoder, channels, bpc, type, rgb_state, computedAlpha, result, resultData, width, bpc_mask,
							 jsquic, channel_r, channel_g, channel_b, buckets_ptrs_r, buckets_ptrs_g, buckets_ptrs_b, correlate_row_r, correlate_row_g,
							 correlate_row_b, computedWidth, xlatL2U, lzeroes, lzeroes8, lzeroes16, lzeroes24,
							 notGRprefixmask, notGRcwlen, nGRcodewords, notGRsuffixlen, eatbits, tabrand, decode_run, bppmask, tabrand_chaos,
							 tabrand_seedmask, usr) {

	var pos = 0;
	var rows_completed = encoder.rows_completed;
	var currentOffset32 = ((rows_completed) * computedWidth / 4);
	var offset = ((rows_completed - 1) * computedWidth);
	while ((jsquic.wmimax > rgb_state.wmidx) && (rgb_state.wmileft <= width)) {
		if (rgb_state.wmileft) {
			uncompress_row_seg(
				encoder,
				pos,
				pos + rgb_state.wmileft,
				bpc,
				bpc_mask,
				type,
				rgb_state,
				computedAlpha,
				result,
				resultData,
				channel_r,
				channel_g,
				channel_b,
				buckets_ptrs_r,
				buckets_ptrs_g,
				buckets_ptrs_b,
				correlate_row_r,
				correlate_row_g,
				correlate_row_b,
				computedWidth,
				xlatL2U,
				lzeroes,
				lzeroes8,
				lzeroes16,
				lzeroes24,
				notGRprefixmask,
				notGRcwlen,
				nGRcodewords,
				notGRsuffixlen,
				eatbits,
				tabrand,
				decode_run,
				bppmask,
				jsquic,
				tabrand_chaos,
				rows_completed,
				tabrand_seedmask,
				offset,
				currentOffset32,
				usr
			);
			pos += rgb_state.wmileft;
			width -= rgb_state.wmileft;
		}

		rgb_state.wmidx++;
		jsquic.set_wm_trigger(rgb_state);
		rgb_state.wmileft = jsquic.wminext;
	}

	if (width) {
		uncompress_row_seg(
			encoder,
			pos,
			pos + width,
			bpc,
			bpc_mask,
			type,
			rgb_state,
			computedAlpha,
			result,
			resultData,
			channel_r,
			channel_g,
			channel_b,
			buckets_ptrs_r,
			buckets_ptrs_g,
			buckets_ptrs_b,
			correlate_row_r,
			correlate_row_g,
			correlate_row_b,
			computedWidth,
			xlatL2U,
			lzeroes,
			lzeroes8,
			lzeroes16,
			lzeroes24,
			notGRprefixmask,
			notGRcwlen,
			nGRcodewords,
			notGRsuffixlen,
			eatbits,
			tabrand,
			decode_run,
			bppmask,
			jsquic,
			tabrand_chaos,
			rows_completed,
			tabrand_seedmask,
			offset,
			currentOffset32,
			usr
		);
		if (jsquic.wmimax > encoder.rgb_state.wmidx) {
			rgb_state.wmileft -= width;
		}
	}
}


function quic_uncompress_row_a(encoder, channels, bpc, type, rgb_state) {
	var bpc_mask = wdi.JSQuic.BPC_MASK[type];
	var pos = 0;
	var width = encoder.width;
	while ((wdi.JSQuic.wmimax > rgb_state.wmidx) && (rgb_state.wmileft <= width)) {
		if (rgb_state.wmileft) {
			uncompress_row_seg_a(
				encoder,
				pos,
				pos + rgb_state.wmileft,
				bpc,
				bpc_mask,
				type,
				rgb_state
			);
			pos += rgb_state.wmileft;
			width -= rgb_state.wmileft;
		}

		rgb_state.wmidx++;
		wdi.JSQuic.set_wm_trigger(rgb_state);
		rgb_state.wmileft = wdi.JSQuic.wminext;
	}

	if (width) {
		uncompress_row_seg_a(
			encoder,
			pos,
			pos + width,
			bpc,
			bpc_mask,
			type,
			rgb_state
		);
		if (wdi.JSQuic.wmimax > encoder.rgb_state.wmidx) {
			rgb_state.wmileft -= width;
		}
	}
}

function SAME_PIXEL_RGB_A(i, result) {

	if (result[i - 4] === result[i] && result[i - 3] === result[i + 1] && result[i - 2] === result[i + 2])
		return true;

	return false;
}

function SAME_PIXEL(i, result) {

	if (result[i - 1] === result[i])
		return true;

	return false;
}

function RLE_PRED_RGB_A(i, encoder, offset, currentOffset, run_index) {
	if (run_index !== i && i > 2) {
		if (SAME_PIXEL_RGB_A(offset, encoder.result)) { //fila de arriba
			var pr = currentOffset + ((i - 1) * 4);
			if (SAME_PIXEL_RGB_A(pr, encoder.result)) { //pixel de la izquierda
				return true;
			}
		}
	}
	return false;
}

function RLE_PRED(i, encoder, offset, currentOffset, run_index) {
	if (run_index !== i && i > 2) {
		if (SAME_PIXEL(offset * 4, encoder.result)) { //fila de arriba
			var pr = currentOffset + i - 1;
			if (SAME_PIXEL(pr * 4, encoder.result)) { //pixel de la izquierda
				return true;
			}
		}
	}
	return false;
}

function uncompress_row_seg(encoder, i, end, bpc, bpc_mask, type, rgb_state, computedAlpha, result, resultData,
							channel_r, channel_g, channel_b, buckets_ptrs_r, buckets_ptrs_g, buckets_ptrs_b, correlate_row_r, correlate_row_g,
							correlate_row_b, computedWidth, xlatL2U, lzeroes, lzeroes8, lzeroes16, lzeroes24, notGRprefixmask, notGRcwlen,
							nGRcodewords, notGRsuffixlen, eatbits, tabrand, decode_run, bppmask, jsquic, tabrand_chaos, rows_completed,
							tabrand_seedmask, offset, currentOffset32, usr) {

	var stopidx = 0;
	var waitmask = bppmask[rgb_state.wmidx];
	var run_index = 0;
	var rle = false;

	//var offset = ((rows_completed-1) * computedWidth);
	//var currentOffset32 = ((rows_completed) * computedWidth/4);

	var i_1, i_4; //for performance improvments

	var pr, pg, pb;

	var prevCorrelatedR, prevCorrelatedG, prevCorrelatedB;
	var ret, codewordlen, l, bits, zeroprefix;

	var cnt = encoder.cnt;
	var pxCnt = encoder.pxCnt;

	var prev_row, i4sub, stopidx_sub1;

	var available_bits, io_word, delta, io_next_word;

	if (!i) {
		pr = UNCOMPRESS_ONE_0(channel_r, encoder, bpc_mask, offset);
		pg = UNCOMPRESS_ONE_0(channel_g, encoder, bpc_mask, offset);
		pb = UNCOMPRESS_ONE_0(channel_b, encoder, bpc_mask, offset);

		prevCorrelatedR = correlate_row_r[0];
		prevCorrelatedG = correlate_row_g[0];
		prevCorrelatedB = correlate_row_b[0];
		//inlined appendPixel
		resultData[pxCnt++] =
			255 << 24 | // alpha
			pb << 16 | // blue
			pg << 8 | // green
			pr; // red
		//cnt += 4;

		if (rgb_state.waitcnt) {
			--rgb_state.waitcnt;
		} else {
			rgb_state.waitcnt = (tabrand.call(jsquic, rgb_state) & waitmask);
			UPDATE_MODEL(0, encoder, bpc, correlate_row_r, correlate_row_g, correlate_row_b);
		}
		stopidx = ++i + rgb_state.waitcnt;
	} else {
		stopidx = i + rgb_state.waitcnt;
		pr = result[cnt - 4];
		pg = result[cnt - 3];
		pb = result[cnt - 2];

		prevCorrelatedR = correlate_row_r[i - 1];
		prevCorrelatedG = correlate_row_g[i - 1];
		prevCorrelatedB = correlate_row_b[i - 1];
	}


	while (true) {
		while (stopidx < end) {
			i_4 = offset + i * 4;
			for (; i <= stopidx; i++) {
				/////// critical part
				//rle = RLE_PRED(i, encoder, ci, currentOffset32, run_index);
				//RLE_PRED INLINE
				//inlined same_pixel, see original rle_pred
				i4sub = i_4 / 4;
				if (resultData[i4sub - 1] === resultData[i4sub]) { //fila de arriba
					prev_row = currentOffset32 + i - 1;
					if (resultData[prev_row - 1] === resultData[prev_row]) { //pixel de la izquierda
						if (run_index !== i && i > 2) {
							rle = true;
							break;
						}
					}
				}


				/////////////////////// INLINING UNCOMPRESS_ONE
				//r
				/////////////////////// INLINING GOLOMB_DECODING
				//ret = golomb_decoding(buckets_ptrs_r[prevCorrelatedR].bestcode,
				//	encoder.io_word, bppmask, notGRprefixmask, notGRcwlen, nGRcodewords, notGRsuffixlen);
				l = buckets_ptrs_r[prevCorrelatedR].bestcode;
				bits = encoder.io_word;
				if (bits > notGRprefixmask[l]) {
					//zeroprefix = cnt_l_zeroes(bits);

					if (bits > 0x007FFFFF) {
						zeroprefix = lzeroes[bits >>> 24];
					} else if (bits > 0x00007FFF) {
						zeroprefix = lzeroes8[((bits >>> 16) & 0x000000ff)];
					} else if (bits > 0x0000007F) {
						zeroprefix = lzeroes16[((bits >>> 8) & 0x000000ff)];
					} else {
						zeroprefix = lzeroes24[(bits & 0x000000ff)];
					}

					codewordlen = zeroprefix + 1 + l;
					prevCorrelatedR = ((zeroprefix << l)) | ((bits >>> (32 - codewordlen)) & bppmask[l]);
				} else {
					codewordlen = notGRcwlen[l];
					prevCorrelatedR = nGRcodewords[l] + ((bits) >>> (32 - codewordlen) & bppmask[notGRsuffixlen[l]]);
				}

				correlate_row_r[i] = prevCorrelatedR;

				pr = ((((xlatL2U[prevCorrelatedR] +
				((pr +
				result[i_4++]) >>> 1)) & bpc_mask)));

				//eatbits(codewordlen, encoder);
				//INLINING EATBITS
				available_bits = encoder.io_available_bits;
				io_word = encoder.io_word;

				delta = available_bits - codewordlen;

				io_word = io_word << codewordlen;

				//enough bits
				if (delta >= 0) {
					io_word = (io_word | encoder.io_next_word >>> delta) >>> 0;
					encoder.io_available_bits = delta;
					encoder.io_word = io_word;
				} else {
					io_next_word = encoder.io_next_word;
					//not enough bits
					delta = -delta; //bits missing
					io_word = (io_word | (io_next_word << delta) >>> 0);

					///////////////////
					//read io word (inlined for perforemance)

					io_next_word = usr[encoder.io_now++];
					//end read io_word
					/////////////////

					available_bits = 32 - delta;
					io_word = (io_word | (io_next_word >>> available_bits)) >>> 0;

					encoder.io_available_bits = available_bits;
					encoder.io_word = io_word;
					encoder.io_next_word = io_next_word;
				}
				//END INLINING

				//g
				///////////////////////////////////////INLINING golomb_decoding

				//ret = golomb_decoding(buckets_ptrs_g[prevCorrelatedG].bestcode,
				//	encoder.io_word, bppmask, notGRprefixmask, notGRcwlen, nGRcodewords, notGRsuffixlen);
				l = buckets_ptrs_g[prevCorrelatedG].bestcode;
				bits = encoder.io_word;

				if (bits > notGRprefixmask[l]) {
					//zeroprefix = cnt_l_zeroes(bits);

					if (bits > 0x007FFFFF) {
						zeroprefix = lzeroes[bits >>> 24];
					} else if (bits > 0x00007FFF) {
						zeroprefix = lzeroes8[((bits >>> 16) & 0x000000ff)];
					} else if (bits > 0x0000007F) {
						zeroprefix = lzeroes16[((bits >>> 8) & 0x000000ff)];
					} else {
						zeroprefix = lzeroes24[(bits & 0x000000ff)];
					}

					codewordlen = zeroprefix + 1 + l;
					prevCorrelatedG = ((zeroprefix << l)) | ((bits >>> (32 - codewordlen)) & bppmask[l]);
				} else {
					codewordlen = notGRcwlen[l];
					prevCorrelatedG = nGRcodewords[l] + ((bits) >>> (32 - codewordlen) & bppmask[notGRsuffixlen[l]]);
				}

				correlate_row_g[i] = prevCorrelatedG;

				pg = ((((xlatL2U[prevCorrelatedG] +
				((pg +
				result[i_4++]) >>> 1)) & bpc_mask)));

				//INLINING EATBITS
				available_bits = encoder.io_available_bits;
				io_word = encoder.io_word;

				delta = available_bits - codewordlen;

				io_word = io_word << codewordlen;

				//enough bits
				if (delta >= 0) {
					io_word = (io_word | encoder.io_next_word >>> delta) >>> 0;
					encoder.io_available_bits = delta;
					encoder.io_word = io_word;
				} else {
					io_next_word = encoder.io_next_word;
					//not enough bits
					delta = -delta; //bits missing
					io_word = (io_word | (io_next_word << delta) >>> 0);

					///////////////////
					//read io word (inlined for perforemance)

					io_next_word = usr[encoder.io_now++];
					//end read io_word
					/////////////////

					available_bits = 32 - delta;
					io_word = (io_word | (io_next_word >>> available_bits)) >>> 0;

					encoder.io_available_bits = available_bits;
					encoder.io_word = io_word;
					encoder.io_next_word = io_next_word;
				}
				//END INLINING

				//b
				////////////////////////////////// INLINING golomb_decoding
				//ret = golomb_decoding(buckets_ptrs_b[prevCorrelatedB].bestcode,
				//	encoder.io_word, bppmask, notGRprefixmask, notGRcwlen, nGRcodewords, notGRsuffixlen);
				l = buckets_ptrs_b[prevCorrelatedB].bestcode;
				bits = encoder.io_word;

				if (bits > notGRprefixmask[l]) {
					//zeroprefix = cnt_l_zeroes(bits);

					if (bits > 0x007FFFFF) {
						zeroprefix = lzeroes[bits >>> 24];
					} else if (bits > 0x00007FFF) {
						zeroprefix = lzeroes8[((bits >>> 16) & 0x000000ff)];
					} else if (bits > 0x0000007F) {
						zeroprefix = lzeroes16[((bits >>> 8) & 0x000000ff)];
					} else {
						zeroprefix = lzeroes24[(bits & 0x000000ff)];
					}

					codewordlen = zeroprefix + 1 + l;
					prevCorrelatedB = ((zeroprefix << l)) | ((bits >>> (32 - codewordlen)) & bppmask[l]);
				} else {
					codewordlen = notGRcwlen[l];
					prevCorrelatedB = nGRcodewords[l] + ((bits) >>> (32 - codewordlen) & bppmask[notGRsuffixlen[l]]);
				}


				correlate_row_b[i] = prevCorrelatedB;

				pb = ((((xlatL2U[prevCorrelatedB] +
				((pb +
				result[i_4++]) >>> 1)) & bpc_mask)));

				//INLINING EATBITS
				available_bits = encoder.io_available_bits;
				io_word = encoder.io_word;

				delta = available_bits - codewordlen;

				io_word = io_word << codewordlen;

				//enough bits
				if (delta >= 0) {
					io_word = (io_word | encoder.io_next_word >>> delta) >>> 0;
					encoder.io_available_bits = delta;
					encoder.io_word = io_word;
				} else {
					io_next_word = encoder.io_next_word;
					//not enough bits
					delta = -delta; //bits missing
					io_word = (io_word | (io_next_word << delta) >>> 0);

					///////////////////
					//read io word (inlined for perforemance)

					io_next_word = usr[encoder.io_now++];
					//end read io_word
					/////////////////

					available_bits = 32 - delta;
					io_word = (io_word | (io_next_word >>> available_bits)) >>> 0;

					encoder.io_available_bits = available_bits;
					encoder.io_word = io_word;
					encoder.io_next_word = io_next_word;
				}
				//END INLINING
				////////////////////// END INLINING

				/**
				 pr = UNCOMPRESS_ONE(channel_r, i, i_1, i_4, bpc_mask, encoder, correlate_row_r, offset, result, 0, xlatL2U, buckets_ptrs_r, pr);
				 pg = UNCOMPRESS_ONE(channel_g, i, i_1, i_4, bpc_mask, encoder, correlate_row_g, offset, result, 1, xlatL2U, buckets_ptrs_g, pg);
				 pb = UNCOMPRESS_ONE(channel_b, i, i_1, i_4, bpc_mask, encoder, correlate_row_b, offset, result, 2, xlatL2U, buckets_ptrs_b, pb);
				 **/


					//this is inlined appendPixel
				resultData[pxCnt++] =
					computedAlpha | // alpha
					pb << 16 | // blue
					pg << 8 | // green
					pr; // red
				//cnt += 4;
				i_4++; //skip alpha
			}
			if (!rle) {
				//UPDATE_MODEL(stopidx, encoder, bpc, correlate_row_r, correlate_row_g, correlate_row_b);
				//inlining update_model
				stopidx_sub1 = stopidx - 1;
				real_update_model(rgb_state, buckets_ptrs_r[correlate_row_r[stopidx_sub1]],
					correlate_row_r[stopidx], bpc);
				real_update_model(rgb_state, buckets_ptrs_g[correlate_row_g[stopidx_sub1]],
					correlate_row_g[stopidx], bpc);
				real_update_model(rgb_state, buckets_ptrs_b[correlate_row_b[stopidx_sub1]],
					correlate_row_b[stopidx], bpc);
				//end inlining

				rgb_state.tabrand_seed++;
				stopidx = i + ((tabrand_chaos[rgb_state.tabrand_seed & tabrand_seedmask]) & waitmask);


			} else {
				break;
			}
		}

		if (!rle) {
			i_4 = offset + i * 4;
			for (; i < end; i++) {
				//ci = offset32+i;
				//rle = RLE_PRED(i, encoder, ci, currentOffset32, run_index);
				//RLE_PRED INLINE
				//inlined same_pixel, see original rle_pred
				i4sub = i_4 / 4;
				if (resultData[i4sub - 1] === resultData[i4sub]) { //fila de arriba
					prev_row = currentOffset32 + i - 1;
					if (resultData[prev_row - 1] === resultData[prev_row]) { //pixel de la izquierda
						if (run_index !== i && i > 2) {
							rle = true;
							break;
						}
					}
				}

				//END INLINE*/


				////////////////////// INLINING UNCOMPRESS_ONE
				//r
				//ret = golomb_decoding(buckets_ptrs_r[prevCorrelatedR].bestcode, encoder.io_word, bppmask, notGRprefixmask, notGRcwlen, nGRcodewords, notGRsuffixlen);
				//prevCorrelatedR = ret[0];
				//codewordlen = ret[1];
				l = buckets_ptrs_r[prevCorrelatedR].bestcode;
				bits = encoder.io_word;

				if (bits > notGRprefixmask[l]) {
					//zeroprefix = cnt_l_zeroes(bits);

					if (bits > 0x007FFFFF) {
						zeroprefix = lzeroes[bits >>> 24];
					} else if (bits > 0x00007FFF) {
						zeroprefix = lzeroes8[((bits >>> 16) & 0x000000ff)];
					} else if (bits > 0x0000007F) {
						zeroprefix = lzeroes16[((bits >>> 8) & 0x000000ff)];
					} else {
						zeroprefix = lzeroes24[(bits & 0x000000ff)];
					}

					codewordlen = zeroprefix + 1 + l;
					prevCorrelatedR = ((zeroprefix << l)) | ((bits >>> (32 - codewordlen)) & bppmask[l]);
				} else {
					codewordlen = notGRcwlen[l];
					prevCorrelatedR = nGRcodewords[l] + ((bits) >>> (32 - codewordlen) & bppmask[notGRsuffixlen[l]]);
				}

				correlate_row_r[i] = prevCorrelatedR;

				pr = ((((xlatL2U[prevCorrelatedR] +
				((pr +
				result[i_4++]) >>> 1)) & bpc_mask)));

				//INLINING EATBITS
				available_bits = encoder.io_available_bits;
				io_word = encoder.io_word;

				delta = available_bits - codewordlen;

				io_word = io_word << codewordlen;

				//enough bits
				if (delta >= 0) {
					io_word = (io_word | encoder.io_next_word >>> delta) >>> 0;
					encoder.io_available_bits = delta;
					encoder.io_word = io_word;
				} else {
					io_next_word = encoder.io_next_word;
					//not enough bits
					delta = -delta; //bits missing
					io_word = (io_word | (io_next_word << delta) >>> 0);

					///////////////////
					//read io word (inlined for perforemance)

					io_next_word = usr[encoder.io_now++];
					//end read io_word
					/////////////////

					available_bits = 32 - delta;
					io_word = (io_word | (io_next_word >>> available_bits)) >>> 0;

					encoder.io_available_bits = available_bits;
					encoder.io_word = io_word;
					encoder.io_next_word = io_next_word;
				}
				//END INLINING

				//g
				//				ret = golomb_decoding(buckets_ptrs_g[prevCorrelatedG].bestcode, encoder.io_word, bppmask, notGRprefixmask, notGRcwlen, nGRcodewords, notGRsuffixlen);
				//				prevCorrelatedG = ret[0];
				//				codewordlen = ret[1];

				l = buckets_ptrs_g[prevCorrelatedG].bestcode;
				bits = encoder.io_word;

				if (bits > notGRprefixmask[l]) {
					//zeroprefix = cnt_l_zeroes(bits);

					if (bits > 0x007FFFFF) {
						zeroprefix = lzeroes[bits >>> 24];
					} else if (bits > 0x00007FFF) {
						zeroprefix = lzeroes8[((bits >>> 16) & 0x000000ff)];
					} else if (bits > 0x0000007F) {
						zeroprefix = lzeroes16[((bits >>> 8) & 0x000000ff)];
					} else {
						zeroprefix = lzeroes24[(bits & 0x000000ff)];
					}

					codewordlen = zeroprefix + 1 + l;
					prevCorrelatedG = ((zeroprefix << l)) | ((bits >>> (32 - codewordlen)) & bppmask[l]);
				} else {
					codewordlen = notGRcwlen[l];
					prevCorrelatedG = nGRcodewords[l] + ((bits) >>> (32 - codewordlen) & bppmask[notGRsuffixlen[l]]);
				}

				correlate_row_g[i] = prevCorrelatedG;

				pg = ((((xlatL2U[prevCorrelatedG] +
				((pg +
				result[i_4++]) >>> 1)) & bpc_mask)));

				//INLINING EATBITS
				available_bits = encoder.io_available_bits;
				io_word = encoder.io_word;

				delta = available_bits - codewordlen;

				io_word = io_word << codewordlen;

				//enough bits
				if (delta >= 0) {
					io_word = (io_word | encoder.io_next_word >>> delta) >>> 0;
					encoder.io_available_bits = delta;
					encoder.io_word = io_word;
				} else {
					io_next_word = encoder.io_next_word;
					//not enough bits
					delta = -delta; //bits missing
					io_word = (io_word | (io_next_word << delta) >>> 0);

					///////////////////
					//read io word (inlined for perforemance)

					io_next_word = usr[encoder.io_now++];
					//end read io_word
					/////////////////

					available_bits = 32 - delta;
					io_word = (io_word | (io_next_word >>> available_bits)) >>> 0;

					encoder.io_available_bits = available_bits;
					encoder.io_word = io_word;
					encoder.io_next_word = io_next_word;
				}
				//END INLINING

				//b
				//				ret = golomb_decoding(buckets_ptrs_b[prevCorrelatedB].bestcode, encoder.io_word, bppmask, notGRprefixmask, notGRcwlen, nGRcodewords, notGRsuffixlen);
				//				prevCorrelatedB = ret[0];
				//				codewordlen = ret[1];
				//

				l = buckets_ptrs_b[prevCorrelatedB].bestcode;
				bits = encoder.io_word;

				if (bits > notGRprefixmask[l]) {
					//zeroprefix = cnt_l_zeroes(bits);

					if (bits > 0x007FFFFF) {
						zeroprefix = lzeroes[bits >>> 24];
					} else if (bits > 0x00007FFF) {
						zeroprefix = lzeroes8[((bits >>> 16) & 0x000000ff)];
					} else if (bits > 0x0000007F) {
						zeroprefix = lzeroes16[((bits >>> 8) & 0x000000ff)];
					} else {
						zeroprefix = lzeroes24[(bits & 0x000000ff)];
					}

					codewordlen = zeroprefix + 1 + l;
					prevCorrelatedB = ((zeroprefix << l)) | ((bits >>> (32 - codewordlen)) & bppmask[l]);
				} else {
					codewordlen = notGRcwlen[l];
					prevCorrelatedB = nGRcodewords[l] + ((bits) >>> (32 - codewordlen) & bppmask[notGRsuffixlen[l]]);
				}
				correlate_row_b[i] = prevCorrelatedB;

				pb = ((((xlatL2U[prevCorrelatedB] +
				((pb +
				result[i_4++]) >>> 1)) & bpc_mask)));

				//INLINING EATBITS
				available_bits = encoder.io_available_bits;
				io_word = encoder.io_word;

				delta = available_bits - codewordlen;

				io_word = io_word << codewordlen;

				//enough bits
				if (delta >= 0) {
					io_word = (io_word | encoder.io_next_word >>> delta) >>> 0;
					encoder.io_available_bits = delta;
					encoder.io_word = io_word;
				} else {
					io_next_word = encoder.io_next_word;
					//not enough bits
					delta = -delta; //bits missing
					io_word = (io_word | (io_next_word << delta) >>> 0);

					///////////////////
					//read io word (inlined for perforemance)

					io_next_word = usr[encoder.io_now++];
					//end read io_word
					/////////////////

					available_bits = 32 - delta;
					io_word = (io_word | (io_next_word >>> available_bits)) >>> 0;

					encoder.io_available_bits = available_bits;
					encoder.io_word = io_word;
					encoder.io_next_word = io_next_word;
				}
				//END INLINING
				///////////////////// END INLINING

				/**
				 pr = UNCOMPRESS_ONE(channel_r, i, i_1, i_4, bpc_mask, encoder, correlate_row_r, offset, result, 0, xlatL2U, buckets_ptrs_r, pr);
				 pg = UNCOMPRESS_ONE(channel_g, i, i_1, i_4, bpc_mask, encoder, correlate_row_g, offset, result, 1, xlatL2U, buckets_ptrs_g, pg);
				 pb = UNCOMPRESS_ONE(channel_b, i, i_1, i_4, bpc_mask, encoder, correlate_row_b, offset, result, 2, xlatL2U, buckets_ptrs_b, pb);
				 **/

					//this is inlined apendPixel
				resultData[pxCnt++] =
					(255 << 24) | // alpha
					(pb << 16) | // blue
					(pg << 8) | // green
					pr; // red
				//cnt += 4;
				i_4++;
			}
			if (!rle) {
				rgb_state.waitcnt = stopidx - end;
				encoder.cnt = pxCnt * 4;
				encoder.pxCnt = pxCnt;
				return;
			}
		}

		///END of critical part

		//RLE
		rgb_state.waitcnt = stopidx - i;
		run_index = i;
		run_end = decode_run(encoder);

		i = run_end + i;
		while (run_end-- > 0) {
			//this is inlined appendPixel
			resultData[pxCnt++] =
				computedAlpha | // alpha
				pb << 16 | // blue
				pg << 8 | // green
				pr; // red
			//cnt += 4;
		}


		if (i === end) {
			encoder.cnt = pxCnt * 4;
			encoder.pxCnt = pxCnt;
			return;
		}

		i_1 = i - 1;
		prevCorrelatedR = correlate_row_r[i_1];
		prevCorrelatedG = correlate_row_g[i_1];
		prevCorrelatedB = correlate_row_b[i_1];

		stopidx = i + rgb_state.waitcnt;
		rle = false;
		//END RLE
	}
}

function uncompress_row_seg_a(encoder, i, end, bpc, bpc_mask, type, rgb_state) {
	var channel_r = encoder.channels[0];
	var channel_g = encoder.channels[1];
	var channel_b = encoder.channels[2];

	var buckets_ptrs_r = channel_r._buckets_ptrs;
	var buckets_ptrs_g = channel_g._buckets_ptrs;
	var buckets_ptrs_b = channel_b._buckets_ptrs;

	var correlate_row_r = channel_r.correlate_row;
	var correlate_row_g = channel_g.correlate_row;
	var correlate_row_b = channel_b.correlate_row;

	var stopidx = 0;

	var waitmask = wdi.JSQuic.bppmask[rgb_state.wmidx];

	var run_index = 0;
	var run_end = 0;

	var rle = false;

	var computedWidth = encoder.computedWidth;

	var offset = ((encoder.rows_completed - 1) * computedWidth);
	var currentOffset = ((encoder.rows_completed) * computedWidth);

	var offset32 = ((encoder.rows_completed - 1) * computedWidth / 4);
	var currentOffset32 = ((encoder.rows_completed) * computedWidth / 4);

	var result = encoder.result;
	var resultData = encoder.resultData;

	var i_1, i_4; //for performance improvments

	var xlatL2U = wdi.xlatL2U;

	var pr, pg, pb;

	var prevCorrelatedR, prevCorrelatedG, prevCorrelatedB;

	var eatbits = encoder.eatbits;
	var tabrand = wdi.JSQuic.tabrand;
	var decode_run = wdi.JSQuic.decode_run;

	var ret, codewordlen, l, bits, zeroprefix;
	var lzeroes = wdi.JSQuic.lzeroes;
	var lzeroes8 = wdi.JSQuic.lzeroes8;
	var lzeroes16 = wdi.JSQuic.lzeroes16;
	var lzeroes24 = wdi.JSQuic.lzeroes24;

	var cnt = encoder.cnt;
	var pxCnt = encoder.pxCnt;

	var bppmask = wdi.JSQuic.bppmask;

	var notGRprefixmask = wdi.notGRprefixmask;
	var notGRcwlen = wdi.notGRcwlen;
	var nGRcodewords = wdi.nGRcodewords;
	var notGRsuffixlen = wdi.notGRsuffixlen;

	var prev_row, i4sub, ci;

	var computedAlpha = 255 << 24;

	if (!i) {
		pr = UNCOMPRESS_ONE_0(channel_r, encoder, bpc_mask, offset);
		pg = UNCOMPRESS_ONE_0(channel_g, encoder, bpc_mask, offset);
		pb = UNCOMPRESS_ONE_0(channel_b, encoder, bpc_mask, offset);

		prevCorrelatedR = correlate_row_r[0];
		prevCorrelatedG = correlate_row_g[0];
		prevCorrelatedB = correlate_row_b[0];
		//inlined appendPixel
		resultData[pxCnt++] =
			(255 << 24) | // alpha
			(pb << 16) | // blue
			(pg << 8) | // green
			pr; // red
		//cnt += 4;

		if (rgb_state.waitcnt) {
			--rgb_state.waitcnt;
		} else {
			rgb_state.waitcnt = (tabrand.call(wdi.JSQuic, rgb_state) & waitmask);
			UPDATE_MODEL(0, encoder, bpc, correlate_row_r, correlate_row_g, correlate_row_b);
		}
		stopidx = ++i + rgb_state.waitcnt;
	} else {
		stopidx = i + rgb_state.waitcnt;
		pr = result[cnt - 4];
		pg = result[cnt - 3];
		pb = result[cnt - 2];

		prevCorrelatedR = correlate_row_r[i - 1];
		prevCorrelatedG = correlate_row_g[i - 1];
		prevCorrelatedB = correlate_row_b[i - 1];
	}


	while (true) {
		while (stopidx < end) {
			i_4 = offset + i * 4;
			for (; i <= stopidx; i++) {
				/////// critical part
				rle = RLE_PRED_RGB_A(i, encoder, i_4, currentOffset, run_index);
				//RLE_PRED INLINE
				/*if(run_index !== i && i > 2) {
				 //inlined same_pixel, see original rle_pred
				 i4sub = i_4/4;
				 if(encoder.resultData[i4sub-1] === encoder.resultData[i4sub]) { //fila de arriba
				 var prev_row = currentOffset32 + i-1;
				 if(encoder.resultData[prev_row-1] === encoder.resultData[prev_row]) { //pixel de la izquierda
				 rle = true;
				 }
				 }
				 }*/
				//END INLINE
				if (rle) break;


				/////////////////////// INLINING UNCOMPRESS_ONE
				//r
				/////////////////////// INLINING GOLOMB_DECODING
				//ret = golomb_decoding(buckets_ptrs_r[prevCorrelatedR].bestcode,
				//	encoder.io_word, bppmask, notGRprefixmask, notGRcwlen, nGRcodewords, notGRsuffixlen);
				l = buckets_ptrs_r[prevCorrelatedR].bestcode;
				bits = encoder.io_word;
				if (bits > notGRprefixmask[l]) {
					zeroprefix = cnt_l_zeroes(bits);
					/*
					 if (bits > 0x007FFFFF) {
					 zeroprefix = lzeroes[bits >>> 24];
					 } else if (bits > 0x00007FFF) {
					 zeroprefix = lzeroes8[((bits >>> 16) & 0x000000ff)];
					 } else if (bits > 0x0000007F) {
					 zeroprefix = lzeroes16[((bits >>> 8) & 0x000000ff) ];
					 } else {
					 zeroprefix = lzeroes24[(bits & 0x000000ff) ];
					 }*/

					codewordlen = zeroprefix + 1 + l;
					prevCorrelatedR = ((zeroprefix << l)) | ((bits >>> (32 - codewordlen)) & bppmask[l]);
				} else {
					codewordlen = notGRcwlen[l];
					prevCorrelatedR = nGRcodewords[l] + ((bits) >>> (32 - codewordlen) & bppmask[notGRsuffixlen[l]]);
				}

				correlate_row_r[i] = prevCorrelatedR;

				pr = ((((xlatL2U[prevCorrelatedR] +
				((pr +
				result[i_4++]) >>> 1)) & bpc_mask)));

				eatbits(codewordlen, encoder);

				//g
				///////////////////////////////////////INLINING golomb_decoding

				//ret = golomb_decoding(buckets_ptrs_g[prevCorrelatedG].bestcode,
				//	encoder.io_word, bppmask, notGRprefixmask, notGRcwlen, nGRcodewords, notGRsuffixlen);
				l = buckets_ptrs_g[prevCorrelatedG].bestcode;
				bits = encoder.io_word;

				if (bits > notGRprefixmask[l]) {
					zeroprefix = cnt_l_zeroes(bits);
					/*
					 if (bits > 0x007FFFFF) {
					 zeroprefix = lzeroes[bits >>> 24];
					 } else if (bits > 0x00007FFF) {
					 zeroprefix = lzeroes8[((bits >>> 16) & 0x000000ff)];
					 } else if (bits > 0x0000007F) {
					 zeroprefix = lzeroes16[((bits >>> 8) & 0x000000ff) ];
					 } else {
					 zeroprefix = lzeroes24[(bits & 0x000000ff) ];
					 }*/

					codewordlen = zeroprefix + 1 + l;
					prevCorrelatedG = ((zeroprefix << l)) | ((bits >>> (32 - codewordlen)) & bppmask[l]);
				} else {
					codewordlen = notGRcwlen[l];
					prevCorrelatedG = nGRcodewords[l] + ((bits) >>> (32 - codewordlen) & bppmask[notGRsuffixlen[l]]);
				}

				correlate_row_g[i] = prevCorrelatedG;

				pg = ((((xlatL2U[prevCorrelatedG] +
				((pg +
				result[i_4++]) >>> 1)) & bpc_mask)));

				eatbits(codewordlen, encoder);

				//b
				////////////////////////////////// INLINING golomb_decoding
				//ret = golomb_decoding(buckets_ptrs_b[prevCorrelatedB].bestcode,
				//	encoder.io_word, bppmask, notGRprefixmask, notGRcwlen, nGRcodewords, notGRsuffixlen);
				l = buckets_ptrs_b[prevCorrelatedB].bestcode;
				bits = encoder.io_word;

				if (bits > notGRprefixmask[l]) {
					zeroprefix = cnt_l_zeroes(bits);
					/*
					 if (bits > 0x007FFFFF) {
					 zeroprefix = lzeroes[bits >>> 24];
					 } else if (bits > 0x00007FFF) {
					 zeroprefix = lzeroes8[((bits >>> 16) & 0x000000ff)];
					 } else if (bits > 0x0000007F) {
					 zeroprefix = lzeroes16[((bits >>> 8) & 0x000000ff) ];
					 } else {
					 zeroprefix = lzeroes24[(bits & 0x000000ff) ];
					 }*/

					codewordlen = zeroprefix + 1 + l;
					prevCorrelatedB = ((zeroprefix << l)) | ((bits >>> (32 - codewordlen)) & bppmask[l]);
				} else {
					codewordlen = notGRcwlen[l];
					prevCorrelatedB = nGRcodewords[l] + ((bits) >>> (32 - codewordlen) & bppmask[notGRsuffixlen[l]]);
				}


				correlate_row_b[i] = prevCorrelatedB;

				pb = ((((xlatL2U[prevCorrelatedB] +
				((pb +
				result[i_4++]) >>> 1)) & bpc_mask)));

				eatbits(codewordlen, encoder);
				////////////////////// END INLINING

				/**
				 pr = UNCOMPRESS_ONE(channel_r, i, i_1, i_4, bpc_mask, encoder, correlate_row_r, offset, result, 0, xlatL2U, buckets_ptrs_r, pr);
				 pg = UNCOMPRESS_ONE(channel_g, i, i_1, i_4, bpc_mask, encoder, correlate_row_g, offset, result, 1, xlatL2U, buckets_ptrs_g, pg);
				 pb = UNCOMPRESS_ONE(channel_b, i, i_1, i_4, bpc_mask, encoder, correlate_row_b, offset, result, 2, xlatL2U, buckets_ptrs_b, pb);
				 **/


					//this is inlined appendPixel
				resultData[pxCnt++] =
					computedAlpha | // alpha
					pb << 16 | // blue
					pg << 8 | // green
					pr; // red
				//cnt += 4;
				i_4++; //skip alpha
			}
			if (!rle) {
				UPDATE_MODEL(stopidx, encoder, bpc, correlate_row_r, correlate_row_g, correlate_row_b);
				stopidx = i + (tabrand.call(wdi.JSQuic, rgb_state) & waitmask);
			} else {
				break;
			}
		}

		if (!rle) {
			i_4 = offset + i * 4;
			for (; i < end; i++) {
				rle = RLE_PRED_RGB_A(i, encoder, i_4, currentOffset, run_index);
				//RLE_PRED INLINE
				/*if(run_index !== i && i > 2) {
				 //inlined same_pixel, see original rle_pred
				 i4sub = i_4/4;
				 if(encoder.resultData[i4sub-1] === encoder.resultData[i4sub]) { //fila de arriba
				 var prev_row = currentOffset32 + i-1;
				 if(encoder.resultData[prev_row-1] === encoder.resultData[prev_row]) { //pixel de la izquierda
				 rle = true;
				 }
				 }
				 }
				 //END INLINE*/
				if (rle) break;


				////////////////////// INLINING UNCOMPRESS_ONE
				//r
				//ret = golomb_decoding(buckets_ptrs_r[prevCorrelatedR].bestcode, encoder.io_word, bppmask, notGRprefixmask, notGRcwlen, nGRcodewords, notGRsuffixlen);
				//prevCorrelatedR = ret[0];
				//codewordlen = ret[1];
				l = buckets_ptrs_r[prevCorrelatedR].bestcode;
				bits = encoder.io_word;

				if (bits > notGRprefixmask[l]) {
					zeroprefix = cnt_l_zeroes(bits);
					/*
					 if (bits > 0x007FFFFF) {
					 zeroprefix = lzeroes[bits >>> 24];
					 } else if (bits > 0x00007FFF) {
					 zeroprefix = lzeroes8[((bits >>> 16) & 0x000000ff)];
					 } else if (bits > 0x0000007F) {
					 zeroprefix = lzeroes16[((bits >>> 8) & 0x000000ff) ];
					 } else {
					 zeroprefix = lzeroes24[(bits & 0x000000ff) ];
					 }*/

					codewordlen = zeroprefix + 1 + l;
					prevCorrelatedR = ((zeroprefix << l)) | ((bits >>> (32 - codewordlen)) & bppmask[l]);
				} else {
					codewordlen = notGRcwlen[l];
					prevCorrelatedR = nGRcodewords[l] + ((bits) >>> (32 - codewordlen) & bppmask[notGRsuffixlen[l]]);
				}

				correlate_row_r[i] = prevCorrelatedR;

				pr = ((((xlatL2U[prevCorrelatedR] +
				((pr +
				result[i_4++]) >>> 1)) & bpc_mask)));

				eatbits(codewordlen, encoder);

				//g
				//				ret = golomb_decoding(buckets_ptrs_g[prevCorrelatedG].bestcode, encoder.io_word, bppmask, notGRprefixmask, notGRcwlen, nGRcodewords, notGRsuffixlen);
				//				prevCorrelatedG = ret[0];
				//				codewordlen = ret[1];

				l = buckets_ptrs_g[prevCorrelatedG].bestcode;
				bits = encoder.io_word;

				if (bits > notGRprefixmask[l]) {
					zeroprefix = cnt_l_zeroes(bits);
					/*
					 if (bits > 0x007FFFFF) {
					 zeroprefix = lzeroes[bits >>> 24];
					 } else if (bits > 0x00007FFF) {
					 zeroprefix = lzeroes8[((bits >>> 16) & 0x000000ff)];
					 } else if (bits > 0x0000007F) {
					 zeroprefix = lzeroes16[((bits >>> 8) & 0x000000ff) ];
					 } else {
					 zeroprefix = lzeroes24[(bits & 0x000000ff) ];
					 }*/

					codewordlen = zeroprefix + 1 + l;
					prevCorrelatedG = ((zeroprefix << l)) | ((bits >>> (32 - codewordlen)) & bppmask[l]);
				} else {
					codewordlen = notGRcwlen[l];
					prevCorrelatedG = nGRcodewords[l] + ((bits) >>> (32 - codewordlen) & bppmask[notGRsuffixlen[l]]);
				}

				correlate_row_g[i] = prevCorrelatedG;

				pg = ((((xlatL2U[prevCorrelatedG] +
				((pg +
				result[i_4++]) >>> 1)) & bpc_mask)));

				eatbits(codewordlen, encoder);

				//b
				//				ret = golomb_decoding(buckets_ptrs_b[prevCorrelatedB].bestcode, encoder.io_word, bppmask, notGRprefixmask, notGRcwlen, nGRcodewords, notGRsuffixlen);
				//				prevCorrelatedB = ret[0];
				//				codewordlen = ret[1];
				//

				l = buckets_ptrs_b[prevCorrelatedB].bestcode;
				bits = encoder.io_word;

				if (bits > notGRprefixmask[l]) {
					zeroprefix = cnt_l_zeroes(bits);
					/*
					 if (bits > 0x007FFFFF) {
					 zeroprefix = lzeroes[bits >>> 24];
					 } else if (bits > 0x00007FFF) {
					 zeroprefix = lzeroes8[((bits >>> 16) & 0x000000ff)];
					 } else if (bits > 0x0000007F) {
					 zeroprefix = lzeroes16[((bits >>> 8) & 0x000000ff) ];
					 } else {
					 zeroprefix = lzeroes24[(bits & 0x000000ff) ];
					 }*/

					codewordlen = zeroprefix + 1 + l;
					prevCorrelatedB = ((zeroprefix << l)) | ((bits >>> (32 - codewordlen)) & bppmask[l]);
				} else {
					codewordlen = notGRcwlen[l];
					prevCorrelatedB = nGRcodewords[l] + ((bits) >>> (32 - codewordlen) & bppmask[notGRsuffixlen[l]]);
				}
				correlate_row_b[i] = prevCorrelatedB;

				pb = ((((xlatL2U[prevCorrelatedB] +
				((pb +
				result[i_4++]) >>> 1)) & bpc_mask)));

				eatbits(codewordlen, encoder);
				///////////////////// END INLINING

				/**
				 pr = UNCOMPRESS_ONE(channel_r, i, i_1, i_4, bpc_mask, encoder, correlate_row_r, offset, result, 0, xlatL2U, buckets_ptrs_r, pr);
				 pg = UNCOMPRESS_ONE(channel_g, i, i_1, i_4, bpc_mask, encoder, correlate_row_g, offset, result, 1, xlatL2U, buckets_ptrs_g, pg);
				 pb = UNCOMPRESS_ONE(channel_b, i, i_1, i_4, bpc_mask, encoder, correlate_row_b, offset, result, 2, xlatL2U, buckets_ptrs_b, pb);
				 **/

					//this is inlined apendPixel
				resultData[pxCnt++] =
					(255 << 24) | // alpha
					(pb << 16) | // blue
					(pg << 8) | // green
					pr; // red
				//cnt += 4;
				i_4++;
			}
			if (!rle) {
				rgb_state.waitcnt = stopidx - end;
				encoder.cnt = pxCnt * 4;
				encoder.pxCnt = pxCnt;
				return;
			}
		}

		///END of critical part

		//RLE
		rgb_state.waitcnt = stopidx - i;
		run_index = i;
		run_end = decode_run(encoder);

		i = run_end + i;
		while (run_end-- > 0) {
			//this is inlined appendPixel
			resultData[pxCnt++] =
				computedAlpha | // alpha
				pb << 16 | // blue
				pg << 8 | // green
				pr; // red
			//cnt += 4;
		}


		if (i === end) {
			encoder.cnt = pxCnt * 4;
			encoder.pxCnt = pxCnt;
			return;
		}

		i_1 = i - 1;
		prevCorrelatedR = correlate_row_r[i_1];
		prevCorrelatedG = correlate_row_g[i_1];
		prevCorrelatedB = correlate_row_b[i_1];

		stopidx = i + rgb_state.waitcnt;
		rle = false;
		//END RLE
	}
}


function quic_uncompress_row0(encoder, channels, bpc, type) {
	var bpc_mask = wdi.JSQuic.BPC_MASK[type];
	var pos = 0;
	var width = encoder.width;
	while ((wdi.JSQuic.wmimax > encoder.rgb_state.wmidx) && (encoder.rgb_state.wmileft <= width)) {
		if (encoder.rgb_state.wmileft) {
			uncompress_row0_seg(
				encoder,
				pos,
				pos + encoder.rgb_state.wmileft,
				wdi.JSQuic.bppmask[encoder.rgb_state.wmidx],
				bpc,
				bpc_mask,
				type
			);
			pos += encoder.rgb_state.wmileft;
			width -= encoder.rgb_state.wmileft;
		}

		encoder.rgb_state.wmidx++;
		wdi.JSQuic.set_wm_trigger(encoder.rgb_state);
		encoder.rgb_state.wmileft = wdi.JSQuic.wminext;
	}

	if (width) {
		uncompress_row0_seg(
			encoder,
			pos,
			pos + width,
			wdi.JSQuic.bppmask[encoder.rgb_state.wmidx],
			bpc,
			bpc_mask,
			type
		);
		if (wdi.JSQuic.wmimax > encoder.rgb_state.wmidx) {
			encoder.rgb_state.wmileft -= width;
		}
	}
}

function uncompress_row0_seg(encoder, i, end, waitmask, bpc, bpc_mask, type) {
	var channel_r = encoder.channels[0];
	var channel_g = encoder.channels[1];
	var channel_b = encoder.channels[2];

	var correlate_row_r = channel_r.correlate_row;
	var correlate_row_g = channel_g.correlate_row;
	var correlate_row_b = channel_b.correlate_row;

	var stopidx = 0;

	var pr, pg, pb;

	if (!i) {
		pr = UNCOMPRESS_ONE_ROW0_0(channel_r);
		pg = UNCOMPRESS_ONE_ROW0_0(channel_g);
		pb = UNCOMPRESS_ONE_ROW0_0(channel_b);

		encoder.appendPixel(pr, pg, pb);

		if (encoder.rgb_state.waitcnt) {
			--encoder.rgb_state.waitcnt;
		} else {
			encoder.rgb_state.waitcnt = (wdi.JSQuic.tabrand(encoder.rgb_state) & waitmask);
			UPDATE_MODEL(0, encoder, bpc, correlate_row_r, correlate_row_g, correlate_row_b);
		}
		stopidx = ++i + encoder.rgb_state.waitcnt;
	} else {
		stopidx = i + encoder.rgb_state.waitcnt;
	}

	while (stopidx < end) {
		for (; i <= stopidx; i++) {
			pr = UNCOMPRESS_ONE_ROW0(channel_r, i, bpc_mask, encoder, correlate_row_r, pr);
			pg = UNCOMPRESS_ONE_ROW0(channel_g, i, bpc_mask, encoder, correlate_row_g, pg);
			pb = UNCOMPRESS_ONE_ROW0(channel_b, i, bpc_mask, encoder, correlate_row_b, pb);

			encoder.appendPixel(pr, pg, pb);
		}
		UPDATE_MODEL(stopidx, encoder, bpc, correlate_row_r, correlate_row_g, correlate_row_b);
		stopidx = i + (wdi.JSQuic.tabrand(encoder.rgb_state) & waitmask);
	}

	for (; i < end; i++) {
		pr = UNCOMPRESS_ONE_ROW0(channel_r, i, bpc_mask, encoder, correlate_row_r, pr);
		pg = UNCOMPRESS_ONE_ROW0(channel_g, i, bpc_mask, encoder, correlate_row_g, pg);
		pb = UNCOMPRESS_ONE_ROW0(channel_b, i, bpc_mask, encoder, correlate_row_b, pb);
		encoder.appendPixel(pr, pg, pb);
	}
	encoder.rgb_state.waitcnt = stopidx - end;
}

function UNCOMPRESS_ONE_0(channel, encoder, bpc_mask, offset) {
	var ret, codewordlen;
	channel.oldFirst = channel.correlate_row[0];
	ret = golomb_decoding(find_bucket(channel,
		channel.correlate_row[0]).bestcode, encoder.io_word, wdi.JSQuic.bppmask, wdi.notGRprefixmask, wdi.notGRcwlen, wdi.nGRcodewords, wdi.notGRsuffixlen);
	channel.correlate_row[0] = ret[0];
	codewordlen = ret[1];
	var residuum = wdi.xlatL2U[channel.correlate_row[0]];
	var prev = encoder.result[offset + channel.num_channel]; //PIXEL_B
	var resultpixel = ((residuum + prev) & bpc_mask);
	encoder.eatbits(codewordlen, encoder);
	return resultpixel;
}

function UNCOMPRESS_ONE(channel, i, i_1, i_4, bpc_mask, encoder, correlate_row, offset, result, num_channel, xlatL2U, buckets_ptrs, prev_pixel) {
	var ret, codewordlen;
	ret = golomb_decoding(buckets_ptrs[correlate_row[i_1]].bestcode, encoder.io_word, wdi.JSQuic.bppmask, wdi.notGRprefixmask, wdi.notGRcwlen, wdi.nGRcodewords, wdi.notGRsuffixlen);

	var data = ret[0];
	codewordlen = ret[1];
	correlate_row[i] = data;

	var ret = ((((xlatL2U[data] +
	((prev_pixel +
	result[offset + (i_4) + num_channel]) >>> 1)) & bpc_mask)));

	encoder.eatbits(codewordlen, encoder);
	return ret;
}


function UNCOMPRESS_ONE_ROW0_0(channel) {
	var ret, codewordlen;
	var encoder = channel.encoder;
	ret = golomb_decoding(find_bucket(channel, 0).bestcode, encoder.io_word, wdi.JSQuic.bppmask, wdi.notGRprefixmask, wdi.notGRcwlen, wdi.nGRcodewords, wdi.notGRsuffixlen);
	channel.correlate_row[0] = ret[0]
	codewordlen = ret[1];
	var ret = wdi.xlatL2U[channel.correlate_row[0]];
	encoder.eatbits(codewordlen, encoder);
	return ret;
}

function UNCOMPRESS_ONE_ROW0(channel, i, bpc_mask, encoder, correlate_row, prev_pixel) {
	var ret, codewordlen;
	ret = golomb_decoding(find_bucket(channel, correlate_row[i - 1]).bestcode, encoder.io_word, wdi.JSQuic.bppmask, wdi.notGRprefixmask, wdi.notGRcwlen, wdi.nGRcodewords, wdi.notGRsuffixlen);
	correlate_row[i] = ret[0];
	codewordlen = ret[1];
	var ret = CORELATE_0(encoder, channel, i, bpc_mask, correlate_row, prev_pixel);
	encoder.eatbits(codewordlen, encoder);
	return ret;
}

function CORELATE_0(encoder, channel, curr, bpc_mask, correlate_row, prev_pixel) {
	return ((wdi.xlatL2U[correlate_row[curr]] + prev_pixel) & bpc_mask);
}

function PIXEL_A(encoder) {
	return encoder.result[encoder.cnt - 4];
}

function PIXEL_B(channel, encoder, pos, offset) {
	return encoder.result[offset + (pos * 4) + channel.num_channel];
}

///////////////////////////////////////////////////////////////////
//LZ

var lzDecompress = {
	LZ_IMAGE_TYPE_INVALID: 0,
	LZ_IMAGE_TYPE_PLT1_LE: 1,
	LZ_IMAGE_TYPE_PLT1_BE: 2,
	LZ_IMAGE_TYPE_PLT4_LE: 3,
	LZ_IMAGE_TYPE_PLT4_BE: 4,
	LZ_IMAGE_TYPE_PLT8: 5,
	LZ_IMAGE_TYPE_RGB16: 6,
	LZ_IMAGE_TYPE_RGB24: 7,
	LZ_IMAGE_TYPE_RGB32: 8,
	LZ_IMAGE_TYPE_RGBA: 9,
	LZ_IMAGE_TYPE_XXXA: 10,
	LZPALETTE_FLAG_PAL_CACHE_ME: 1,
	LZPALETTE_FLAG_PAL_FROM_CACHE: 2,
	LZPALETTE_FLAG_TOP_DOWN: 4,
	PLT_PIXELS_PER_BYTE: [0, 8, 8, 2, 2, 1],
	PLT1_MASK: [1, 2, 4, 8, 16, 32, 64, 128],

	lz_rgb32_decompress_rgb_opaque_reverse: function(arr) {
		//TODO: global alpha and uncouple code

		var in_buf = new Uint8Array(arr);

		var type = in_buf[2];
		var low = in_buf[5] * 256 + in_buf[4]; // 256 = Math.pow(16, 2)
		var high = in_buf[7] * 256 + in_buf[6]; // 256 = Math.pow(16, 2)
		var len = high * 65536 + low; // 65536 = Math.pow(16,4)
		var buf = new ArrayBuffer(len);
		var data = new Uint32Array(buf);
		var view = new DataView(arr);
		var width = view.getUint32(8);
		var height = view.getUint32(12);
		var out_buf_len = len / 4 -1;
		var op = out_buf_len;
		var code, ref, ofs, b;
		var aux;
		var ctrl = in_buf[16];
		var encoder = 16; //padding

		while (op >= 0) {

			ctrl = in_buf[encoder++];
			//if ctrl is 0, there is no way for len to be > 0
			if (ctrl != 0 && (len = ctrl >> 5)!=0) { //>=32
				ref = op; //there is a reference to past bytes, the reference will be
				//provided as an offset to our position
				ofs = (ctrl & 31) << 8; //get the last 5 bits from ctrl

				if (len == 7) {
					do {
						code = in_buf[encoder++];
						len += code;
					} while (code == 255);
				}

				ofs += in_buf[encoder++];
				if (ofs == 0) {
					aux = data[ref+1]; //if osset is 0...it means just the prior pixel copied over and over....
					//in reverse mode, the prior pixel is just the next pixel to the right
					while(len > 9) {
						data[op] = aux;
						data[op-1] = aux;
						data[op-2] = aux;
						data[op-3] = aux;
						data[op-4] = aux;
						data[op-5] = aux;
						data[op-6] = aux;
						data[op-7] = aux;
						data[op-8] = aux;
						data[op-9] = aux;
						op-=10;
						len -= 10;
					}

					while (len-- != 0) {
						data[op--] = aux;
					}
				} else {
					if (ofs == 8191) { //check if all the bits in ofs are 1, then get two more bytes
						ofs += (in_buf[encoder] << 8) + in_buf[encoder+1];
						encoder += 2;
					}

					ref += ofs + 1;

					while(len > 9) {
						data[op] = data[ref];
						data[op-1] = data[ref-1];
						data[op-2] = data[ref-2];
						data[op-3] = data[ref-3];
						data[op-4] = data[ref-4];
						data[op-5] = data[ref-5];
						data[op-6] = data[ref-6];
						data[op-7] = data[ref-7];
						data[op-8] = data[ref-8];
						data[op-9] = data[ref-9];
						op-=10;
						len -= 10;
						ref -= 10;
					}

					while (len-- !== 0) {
						data[op--] = data[ref--];
					}
				}
			} else {
				while(ctrl > 9) {
					data[op] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
					data[op-1] = 4278190080 | in_buf[encoder+3] << 16 | in_buf[encoder+4] << 8 | in_buf[encoder+5];
					data[op-2] = 4278190080 | in_buf[encoder+6] << 16 |	in_buf[encoder+7] << 8 | in_buf[encoder+8];
					data[op-3] = 4278190080 | in_buf[encoder+9] << 16 | in_buf[encoder+10] << 8 | in_buf[encoder+11];
					data[op-4] = 4278190080 | in_buf[encoder+12] << 16 | in_buf[encoder+13] << 8 | in_buf[encoder+14];
					data[op-5] = 4278190080 | in_buf[encoder+15] << 16 | in_buf[encoder+16] << 8 | in_buf[encoder+17];
					data[op-6] = 4278190080 | in_buf[encoder+18] << 16 | in_buf[encoder+19] << 8 | in_buf[encoder+20];
					data[op-7] = 4278190080 | in_buf[encoder+21] << 16 | in_buf[encoder+22] << 8 | in_buf[encoder+23];
					data[op-8] = 4278190080 | in_buf[encoder+24] << 16 | in_buf[encoder+25] << 8 | in_buf[encoder+26];
					data[op-9] = 4278190080 | in_buf[encoder+27] << 16 | in_buf[encoder+28] << 8 | in_buf[encoder+29];
					encoder += 30;
					op -= 10;
					ctrl -= 10;
				}

				if(ctrl != 0) {
					if(ctrl == 9) {
						data[op] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
						data[op-1] = 4278190080 | in_buf[encoder+3] << 16 | in_buf[encoder+4] << 8 | in_buf[encoder+5];
						data[op-2] = 4278190080 | in_buf[encoder+6] << 16 |	in_buf[encoder+7] << 8 | in_buf[encoder+8];
						data[op-3] = 4278190080 | in_buf[encoder+9] << 16 | in_buf[encoder+10] << 8 | in_buf[encoder+11];
						data[op-4] = 4278190080 | in_buf[encoder+12] << 16 | in_buf[encoder+13] << 8 | in_buf[encoder+14];
						data[op-5] = 4278190080 | in_buf[encoder+15] << 16 | in_buf[encoder+16] << 8 | in_buf[encoder+17];
						data[op-6] = 4278190080 | in_buf[encoder+18] << 16 | in_buf[encoder+19] << 8 | in_buf[encoder+20];
						data[op-7] = 4278190080 | in_buf[encoder+21] << 16 | in_buf[encoder+22] << 8 | in_buf[encoder+23];
						data[op-8] = 4278190080 | in_buf[encoder+24] << 16 | in_buf[encoder+25] << 8 | in_buf[encoder+26];
						encoder += 27;
						op -= 9;
					} else if(ctrl == 8) {
						data[op] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
						data[op-1] = 4278190080 | in_buf[encoder+3] << 16 | in_buf[encoder+4] << 8 | in_buf[encoder+5];
						data[op-2] = 4278190080 | in_buf[encoder+6] << 16 |	in_buf[encoder+7] << 8 | in_buf[encoder+8];
						data[op-3] = 4278190080 | in_buf[encoder+9] << 16 | in_buf[encoder+10] << 8 | in_buf[encoder+11];
						data[op-4] = 4278190080 | in_buf[encoder+12] << 16 | in_buf[encoder+13] << 8 | in_buf[encoder+14];
						data[op-5] = 4278190080 | in_buf[encoder+15] << 16 | in_buf[encoder+16] << 8 | in_buf[encoder+17];
						data[op-6] = 4278190080 | in_buf[encoder+18] << 16 | in_buf[encoder+19] << 8 | in_buf[encoder+20];
						data[op-7] = 4278190080 | in_buf[encoder+21] << 16 | in_buf[encoder+22] << 8 | in_buf[encoder+23];
						encoder += 24;
						op -= 8;
					} else if(ctrl == 7) {
						data[op] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
						data[op-1] = 4278190080 | in_buf[encoder+3] << 16 | in_buf[encoder+4] << 8 | in_buf[encoder+5];
						data[op-2] = 4278190080 | in_buf[encoder+6] << 16 |	in_buf[encoder+7] << 8 | in_buf[encoder+8];
						data[op-3] = 4278190080 | in_buf[encoder+9] << 16 | in_buf[encoder+10] << 8 | in_buf[encoder+11];
						data[op-4] = 4278190080 | in_buf[encoder+12] << 16 | in_buf[encoder+13] << 8 | in_buf[encoder+14];
						data[op-5] = 4278190080 | in_buf[encoder+15] << 16 | in_buf[encoder+16] << 8 | in_buf[encoder+17];
						data[op-6] = 4278190080 | in_buf[encoder+18] << 16 | in_buf[encoder+19] << 8 | in_buf[encoder+20];
						encoder += 21;
						op -= 7;
					} else if(ctrl == 6) {
						data[op] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
						data[op-1] = 4278190080 | in_buf[encoder+3] << 16 | in_buf[encoder+4] << 8 | in_buf[encoder+5];
						data[op-2] = 4278190080 | in_buf[encoder+6] << 16 |	in_buf[encoder+7] << 8 | in_buf[encoder+8];
						data[op-3] = 4278190080 | in_buf[encoder+9] << 16 | in_buf[encoder+10] << 8 | in_buf[encoder+11];
						data[op-4] = 4278190080 | in_buf[encoder+12] << 16 | in_buf[encoder+13] << 8 | in_buf[encoder+14];
						data[op-5] = 4278190080 | in_buf[encoder+15] << 16 | in_buf[encoder+16] << 8 | in_buf[encoder+17];
						encoder += 18;
						op -= 6;
					} else if(ctrl == 5) {
						data[op] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
						data[op-1] = 4278190080 | in_buf[encoder+3] << 16 | in_buf[encoder+4] << 8 | in_buf[encoder+5];
						data[op-2] = 4278190080 | in_buf[encoder+6] << 16 |	in_buf[encoder+7] << 8 | in_buf[encoder+8];
						data[op-3] = 4278190080 | in_buf[encoder+9] << 16 | in_buf[encoder+10] << 8 | in_buf[encoder+11];
						data[op-4] = 4278190080 | in_buf[encoder+12] << 16 | in_buf[encoder+13] << 8 | in_buf[encoder+14];
						encoder += 15;
						op -= 5;
					} else if(ctrl == 4) {
						data[op] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
						data[op-1] = 4278190080 | in_buf[encoder+3] << 16 | in_buf[encoder+4] << 8 | in_buf[encoder+5];
						data[op-2] = 4278190080 | in_buf[encoder+6] << 16 |	in_buf[encoder+7] << 8 | in_buf[encoder+8];
						data[op-3] = 4278190080 | in_buf[encoder+9] << 16 | in_buf[encoder+10] << 8 | in_buf[encoder+11];
						encoder += 12;
						op -= 4;
					} else if(ctrl == 3) {
						data[op] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
						data[op-1] = 4278190080 | in_buf[encoder+3] << 16 | in_buf[encoder+4] << 8 | in_buf[encoder+5];
						data[op-2] = 4278190080 | in_buf[encoder+6] << 16 |	in_buf[encoder+7] << 8 | in_buf[encoder+8];
						encoder += 9;
						op -= 3;
					} else if(ctrl == 2) {
						data[op] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
						data[op-1] = 4278190080 | in_buf[encoder+3] << 16 | in_buf[encoder+4] << 8 | in_buf[encoder+5];
						encoder += 6;
						op -= 2;
					} else if(ctrl == 1) {
						data[op--] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
						encoder += 3;
					}
				}

				data[op--] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
				encoder+=3;
			}
		}

		//reverse buf
		//while, line by line
		var left, right, line, temporary;
		var length = width-1;
		while(height--) {
			line = new Uint32Array(buf,height*width*4, width);
			left = 0;
			right = length;
			while (left < right)
			{
				var temporary = line[left];
				line[left++] = line[right];
				line[right--] = temporary;
			}
		}
		return buf;
	},

	lz_rgb32_decompress_rgb: function(arr) {
		//TODO: global alpha and uncouple code
		var op = 0;
		var in_buf = new Uint8Array(arr);

		var opaque = in_buf[1];
		var type = in_buf[2];
		var top_down = in_buf[3];
		if(opaque && !top_down) {
			return lzDecompress.lz_rgb32_decompress_rgb_opaque_reverse(arr);
		}
		var low = in_buf[5] * 256 + in_buf[4]; // 256 = Math.pow(16, 2)
		var high = in_buf[7] * 256 + in_buf[6]; // 256 = Math.pow(16, 2)
		var len = high * 65536 + low; // 65536 = Math.pow(16,4)
		var buf = new ArrayBuffer(len);
		var data = new Uint32Array(buf);
		var out_buf_len = len / 4;
		var code, ref, ofs, b;
		var op_4, aux;
		var ctrl = in_buf[16];
		var offsetView;
		var encoder = 16; //padding

		while (op != out_buf_len) {

			ctrl = in_buf[encoder++];
			//if ctrl is 0, there is no way for len to be > 0
			if (ctrl != 0 && (len = ctrl >> 5)!=0) { //>=32
				ref = op;
				ofs = (ctrl & 31) << 8; //get the last 5 bits from ctrl

				if (len == 7) {
					do {
						code = in_buf[encoder++];
						len += code;
					} while (code == 255);
				}

				ofs += in_buf[encoder++];

				if (ofs == 0) {
					aux = data[--ref];
					while(len > 9) {
						data[op] = aux;
						data[op+1] = aux;
						data[op+2] = aux;
						data[op+3] = aux;
						data[op+4] = aux;
						data[op+5] = aux;
						data[op+6] = aux;
						data[op+7] = aux;
						data[op+8] = aux;
						data[op+9] = aux;
						op+=10;
						len -= 10;
					}


					while (len-- != 0) {
						data[op++] = aux;
					}


				} else {
					if (ofs == 8191) { //check if all the bits in ofs are 1, then get two more bytes
						ofs += (in_buf[encoder] << 8) + in_buf[encoder+1];
						encoder += 2;
					}

					ref -= ofs + 1;
					//if the copy from array to array is bigger than 100 (tested using benchmark) its cheaper to
					//create a view and copy with set. If the copy is less than 100, then its cheaper
					//to just iterate it.
					if(len > 100 && ref+len < op) {
						offsetView = new Uint32Array(buf, ref*4, len);
						data.set(offsetView,op);
						op += len;
						ref += len;
					} else {
						while(len > 9) {
							data[op] = data[ref];
							data[op+1] = data[ref+1];
							data[op+2] = data[ref+2];
							data[op+3] = data[ref+3];
							data[op+4] = data[ref+4];
							data[op+5] = data[ref+5];
							data[op+6] = data[ref+6];
							data[op+7] = data[ref+7];
							data[op+8] = data[ref+8];
							data[op+9] = data[ref+9];
							op+=10;
							len -= 10;
							ref += 10;
						}

						while (len-- !== 0) {
							data[op++] = data[ref++];
						}

					}

				}
			} else {
				while(ctrl > 9) {
					data[op] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
					data[op+1] = 4278190080 | in_buf[encoder+3] << 16 | in_buf[encoder+4] << 8 | in_buf[encoder+5];
					data[op+2] = 4278190080 | in_buf[encoder+6] << 16 |	in_buf[encoder+7] << 8 | in_buf[encoder+8];
					data[op+3] = 4278190080 | in_buf[encoder+9] << 16 | in_buf[encoder+10] << 8 | in_buf[encoder+11];
					data[op+4] = 4278190080 | in_buf[encoder+12] << 16 | in_buf[encoder+13] << 8 | in_buf[encoder+14];
					data[op+5] = 4278190080 | in_buf[encoder+15] << 16 | in_buf[encoder+16] << 8 | in_buf[encoder+17];
					data[op+6] = 4278190080 | in_buf[encoder+18] << 16 | in_buf[encoder+19] << 8 | in_buf[encoder+20];
					data[op+7] = 4278190080 | in_buf[encoder+21] << 16 | in_buf[encoder+22] << 8 | in_buf[encoder+23];
					data[op+8] = 4278190080 | in_buf[encoder+24] << 16 | in_buf[encoder+25] << 8 | in_buf[encoder+26];
					data[op+9] = 4278190080 | in_buf[encoder+27] << 16 | in_buf[encoder+28] << 8 | in_buf[encoder+29];
					encoder += 30;
					op += 10;
					ctrl -= 10;
				}

				//if we are just out of the above loop, ctrl is 9, so do the 9 in a row
				if(ctrl != 0) {
					if(ctrl == 9) {
						data[op] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
						data[op+1] = 4278190080 | in_buf[encoder+3] << 16 | in_buf[encoder+4] << 8 | in_buf[encoder+5];
						data[op+2] = 4278190080 | in_buf[encoder+6] << 16 |	in_buf[encoder+7] << 8 | in_buf[encoder+8];
						data[op+3] = 4278190080 | in_buf[encoder+9] << 16 | in_buf[encoder+10] << 8 | in_buf[encoder+11];
						data[op+4] = 4278190080 | in_buf[encoder+12] << 16 | in_buf[encoder+13] << 8 | in_buf[encoder+14];
						data[op+5] = 4278190080 | in_buf[encoder+15] << 16 | in_buf[encoder+16] << 8 | in_buf[encoder+17];
						data[op+6] = 4278190080 | in_buf[encoder+18] << 16 | in_buf[encoder+19] << 8 | in_buf[encoder+20];
						data[op+7] = 4278190080 | in_buf[encoder+21] << 16 | in_buf[encoder+22] << 8 | in_buf[encoder+23];
						data[op+8] = 4278190080 | in_buf[encoder+24] << 16 | in_buf[encoder+25] << 8 | in_buf[encoder+26];
						encoder += 27;
						op += 9;
					} else if(ctrl == 8) {
						data[op] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
						data[op+1] = 4278190080 | in_buf[encoder+3] << 16 | in_buf[encoder+4] << 8 | in_buf[encoder+5];
						data[op+2] = 4278190080 | in_buf[encoder+6] << 16 |	in_buf[encoder+7] << 8 | in_buf[encoder+8];
						data[op+3] = 4278190080 | in_buf[encoder+9] << 16 | in_buf[encoder+10] << 8 | in_buf[encoder+11];
						data[op+4] = 4278190080 | in_buf[encoder+12] << 16 | in_buf[encoder+13] << 8 | in_buf[encoder+14];
						data[op+5] = 4278190080 | in_buf[encoder+15] << 16 | in_buf[encoder+16] << 8 | in_buf[encoder+17];
						data[op+6] = 4278190080 | in_buf[encoder+18] << 16 | in_buf[encoder+19] << 8 | in_buf[encoder+20];
						data[op+7] = 4278190080 | in_buf[encoder+21] << 16 | in_buf[encoder+22] << 8 | in_buf[encoder+23];
						encoder += 24;
						op += 8;
					} else if(ctrl == 7) {
						data[op] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
						data[op+1] = 4278190080 | in_buf[encoder+3] << 16 | in_buf[encoder+4] << 8 | in_buf[encoder+5];
						data[op+2] = 4278190080 | in_buf[encoder+6] << 16 |	in_buf[encoder+7] << 8 | in_buf[encoder+8];
						data[op+3] = 4278190080 | in_buf[encoder+9] << 16 | in_buf[encoder+10] << 8 | in_buf[encoder+11];
						data[op+4] = 4278190080 | in_buf[encoder+12] << 16 | in_buf[encoder+13] << 8 | in_buf[encoder+14];
						data[op+5] = 4278190080 | in_buf[encoder+15] << 16 | in_buf[encoder+16] << 8 | in_buf[encoder+17];
						data[op+6] = 4278190080 | in_buf[encoder+18] << 16 | in_buf[encoder+19] << 8 | in_buf[encoder+20];
						encoder += 21;
						op += 7;
					} else if(ctrl == 6) {
						data[op] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
						data[op+1] = 4278190080 | in_buf[encoder+3] << 16 | in_buf[encoder+4] << 8 | in_buf[encoder+5];
						data[op+2] = 4278190080 | in_buf[encoder+6] << 16 |	in_buf[encoder+7] << 8 | in_buf[encoder+8];
						data[op+3] = 4278190080 | in_buf[encoder+9] << 16 | in_buf[encoder+10] << 8 | in_buf[encoder+11];
						data[op+4] = 4278190080 | in_buf[encoder+12] << 16 | in_buf[encoder+13] << 8 | in_buf[encoder+14];
						data[op+5] = 4278190080 | in_buf[encoder+15] << 16 | in_buf[encoder+16] << 8 | in_buf[encoder+17];
						encoder += 18;
						op += 6;
					} else if(ctrl == 5) {
						data[op] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
						data[op+1] = 4278190080 | in_buf[encoder+3] << 16 | in_buf[encoder+4] << 8 | in_buf[encoder+5];
						data[op+2] = 4278190080 | in_buf[encoder+6] << 16 |	in_buf[encoder+7] << 8 | in_buf[encoder+8];
						data[op+3] = 4278190080 | in_buf[encoder+9] << 16 | in_buf[encoder+10] << 8 | in_buf[encoder+11];
						data[op+4] = 4278190080 | in_buf[encoder+12] << 16 | in_buf[encoder+13] << 8 | in_buf[encoder+14];
						encoder += 15;
						op += 5;
					} else if(ctrl == 4) {
						data[op] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
						data[op+1] = 4278190080 | in_buf[encoder+3] << 16 | in_buf[encoder+4] << 8 | in_buf[encoder+5];
						data[op+2] = 4278190080 | in_buf[encoder+6] << 16 |	in_buf[encoder+7] << 8 | in_buf[encoder+8];
						data[op+3] = 4278190080 | in_buf[encoder+9] << 16 | in_buf[encoder+10] << 8 | in_buf[encoder+11];
						encoder += 12;
						op += 4;
					} else if(ctrl == 3) {
						data[op] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
						data[op+1] = 4278190080 | in_buf[encoder+3] << 16 | in_buf[encoder+4] << 8 | in_buf[encoder+5];
						data[op+2] = 4278190080 | in_buf[encoder+6] << 16 |	in_buf[encoder+7] << 8 | in_buf[encoder+8];
						encoder += 9;
						op += 3;
					} else if(ctrl == 2) {
						data[op] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
						data[op+1] = 4278190080 | in_buf[encoder+3] << 16 | in_buf[encoder+4] << 8 | in_buf[encoder+5];
						encoder += 6;
						op += 2;
					} else if(ctrl == 1) {
						data[op++] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
						encoder += 3;
					}
				}

				data[op++] = 4278190080 | in_buf[encoder] << 16 | in_buf[encoder+1] << 8 | in_buf[encoder+2];
				encoder+=3;
			}
		}

		if (type === this.LZ_IMAGE_TYPE_RGBA && !opaque) {
			var buf8 = new Uint8Array(buf);

			op = 0;
			ctrl = null;
			//encoder--;
			for (ctrl = in_buf[encoder++]; op < out_buf_len; ctrl = in_buf[encoder++]) {
				ref = op;
				len = ctrl >> 5;
				ofs = ((ctrl & 31) << 8);
				op_4 = op * 4;

				if (ctrl >= 32) {

					code;
					len--;

					if (len === 7 - 1) {
						do {
							code = in_buf[encoder++];
							len += code;
						} while (code === 255);
					}
					code = in_buf[encoder++];
					ofs += code;


					if (code === 255) {
						if ((ofs - code) === (31 << 8)) {
							ofs = in_buf[encoder++] << 8;
							ofs += in_buf[encoder++];
							ofs += 8191;
						}
					}
					len += 3;

					ofs += 1;

					ref -= ofs;
					if (ref === (op - 1)) { //plt4/1 what?
						b = ref;

						for (; len; --len) {
							op_4 = op * 4;
							//COPY_PIXEL
							buf8[(op_4) + 3] = buf8[(b * 4) + 3];

							op++;
						}
					} else {

						for (; len; --len) {
							//COPY_REF_PIXEL
							op_4 = op * 4;
							buf8[(op_4) + 3] = buf8[(ref * 4) + 3];

							op++;
							ref++;
						}
					}
				} else {
					//COPY_COMP_PIXEL
					ctrl++;
					buf8[(op_4) + 3] = in_buf[encoder++];
					op++;


					for (--ctrl; ctrl; ctrl--) {
						//COPY_COMP_PIXEL
						op_4 = op * 4; // faster?
						buf8[(op_4) + 3] = in_buf[encoder++];
						op++;
					}
				}
			}
		}
		return buf;
	}
};

if (wdi.LZSS) {
	wdi.LZSS.lz_rgb32_decompress_rgb = lzDecompress.lz_rgb32_decompress_rgb
} else {
// if (!wdi.LZSS) {
	wdi.LZSS = lzDecompress;
}
