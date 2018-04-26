function golomb_code_len(n, l) {
    if (n < wdi.nGRcodewords[l]) {
        return (n >>> l) + 1 + l;
    } else {
        return wdi.notGRcwlen[l];
    }
}

function golomb_decoding(l, bits, bppmask) {
	var cwlen;
	var result;
    if (bits > wdi.notGRprefixmask[l]) {
        var zeroprefix = cnt_l_zeroes(bits);
        cwlen = zeroprefix + 1 + l;            
        result = ( (zeroprefix << l) >>> 0) | ((bits >>> (32 - cwlen)) & bppmask[l]);
    } else {
        cwlen = wdi.notGRcwlen[l];
        result = wdi.nGRcodewords[l] + ((bits) >>> (32 - cwlen) & bppmask[wdi.notGRsuffixlen[l]]);
    }
	return [result,cwlen];
}

/* update the bucket using just encoded curval */
function real_update_model(state, bucket, curval, bpp) {
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
        for (i = 0; i < bpp; i++) {
            pcounters[i] >>>= 1;
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
	if(val===undefined) {
		val=channel.oldFirst;
	}
    return channel._buckets_ptrs[val];
}