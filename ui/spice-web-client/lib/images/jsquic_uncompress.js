function QUIC_UNCOMPRESS_RGB(encoder, channels, bpc, type) {
	quic_uncompress_row0(encoder, channels, bpc, type);
	encoder.row_completed();
	var rgb_state = encoder.rgb_state;
	var height = encoder.height;
	for (var row = 1; row < height; row++) {
		quic_uncompress_row(encoder, channels, bpc, type, rgb_state);
		encoder.row_completed();
	}
}


function quic_uncompress_row(encoder, channels, bpc, type, rgb_state) {
	var bpc_mask = wdi.JSQuic.BPC_MASK[type];
	var pos = 0;
	var width = encoder.width;
    while ((wdi.JSQuic.wmimax > rgb_state.wmidx) && (rgb_state.wmileft <= width)) {
        if (rgb_state.wmileft) {
            uncompress_row_seg(
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
		uncompress_row_seg(
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

function SAME_PIXEL(i, result) {
	if(result[i-4] === result[i] && result[i-3] === result[i+1] &&
			result[i-2] === result[i+2]) {
		return true;
	}
	return false;
}

function RLE_PRED(i, encoder, offset, currentOffset, run_index) {
	if(run_index !== i && i > 2) { 
		if(SAME_PIXEL(offset, encoder.result)) { //fila de arriba
			var pr = currentOffset + ((i-1)*4);
			if(SAME_PIXEL(pr, encoder.result)) { //pixel de la izquierda
				return true;
			}
		}
	}
	return false;
}

function uncompress_row_seg(encoder, i, end, bpc, bpc_mask, type, rgb_state) {
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
	
	var offset = ((encoder.rows_completed-1) * computedWidth);
	var currentOffset = ((encoder.rows_completed) * computedWidth);
	
	var result = encoder.result;
	var resultData = encoder.resultData;
	
	var i_1,i_4; //for performance improvments
	
	var xlatL2U = wdi.xlatL2U;
	
	var pr, pg, pb;
	
	var prevCorrelatedR, prevCorrelatedG, prevCorrelatedB;
	
	var eatbits = encoder.eatbits;
	var tabrand = wdi.JSQuic.tabrand;
	var decode_run = wdi.JSQuic.decode_run;
	
	var ret, codewordlen;
	
	var cnt = encoder.cnt;
	var pxCnt = encoder.pxCnt;
	
	var bppmask = wdi.JSQuic.bppmask;

	if (!i) {
        pr = UNCOMPRESS_ONE_0(channel_r, encoder, bpc_mask, offset);
        pg = UNCOMPRESS_ONE_0(channel_g, encoder, bpc_mask, offset);
        pb = UNCOMPRESS_ONE_0(channel_b, encoder, bpc_mask, offset);
		
		prevCorrelatedR = correlate_row_r[0];
		prevCorrelatedG = correlate_row_g[0];
		prevCorrelatedB = correlate_row_b[0];
		//inlined appendPixel
		resultData[pxCnt++] =
			(255   << 24) |    // alpha
			(pb << 16) |    // blue
			(pg <<  8) |    // green
			 pr;            // red
		cnt += 4;

        if (rgb_state.waitcnt) {
            --rgb_state.waitcnt;
        } else {
            rgb_state.waitcnt = (tabrand.call(wdi.JSQuic, rgb_state) & waitmask);
            UPDATE_MODEL(0, encoder, bpc, correlate_row_r, correlate_row_g, correlate_row_b);
        }
        stopidx = ++i + rgb_state.waitcnt;
    } else {
        stopidx = i + rgb_state.waitcnt;
		pr = result[cnt-4];
		pg = result[cnt-3];
		pb = result[cnt-2];
		
		prevCorrelatedR = correlate_row_r[i-1];
		prevCorrelatedG = correlate_row_g[i-1];
		prevCorrelatedB = correlate_row_b[i-1];
    }
	
	while(true) {
		while (stopidx < end) {
			i_4 = offset + i*4;
			for (; i <= stopidx; i++) {
				
				rle = RLE_PRED(i, encoder, i_4, currentOffset, run_index);
				
				if(rle) break;
				
				i_1 = i-1;

				/////////////////////// INLINING UNCOMPRESS_ONE
				//r
 				ret = golomb_decoding(buckets_ptrs_r[prevCorrelatedR].bestcode, 
					encoder.io_word, bppmask);
					
				prevCorrelatedR = ret[0];
				codewordlen = ret[1];

				correlate_row_r[i] = prevCorrelatedR;

				pr = ((((xlatL2U[prevCorrelatedR] + 
					((pr + 
					result[i_4]) >>> 1)) 
					& bpc_mask
				)));

				eatbits.call(encoder, codewordlen);
				
				//g
				ret = golomb_decoding(buckets_ptrs_g[prevCorrelatedG].bestcode, 
					encoder.io_word, bppmask);
					
				prevCorrelatedG = ret[0];
				codewordlen = ret[1];

				correlate_row_g[i] = prevCorrelatedG;

				pg = ((((xlatL2U[prevCorrelatedG] + 
					((pg + 
					result[i_4 + 1]) >>> 1)) 
					& bpc_mask
				)));

				eatbits.call(encoder, codewordlen);
				
				//b
				ret = golomb_decoding(buckets_ptrs_b[prevCorrelatedB].bestcode, 
					encoder.io_word, bppmask);
					
				prevCorrelatedB = ret[0];
				codewordlen = ret[1];

				correlate_row_b[i] = prevCorrelatedB;

				pb = ((((xlatL2U[prevCorrelatedB] + 
					((pb + 
					result[i_4 + 2]) >>> 1)) 
					& bpc_mask
				)));

				eatbits.call(encoder, codewordlen);
				////////////////////// END INLINING
				
				/** 
				pr = UNCOMPRESS_ONE(channel_r, i, i_1, i_4, bpc_mask, encoder, correlate_row_r, offset, result, 0, xlatL2U, buckets_ptrs_r, pr);	
				pg = UNCOMPRESS_ONE(channel_g, i, i_1, i_4, bpc_mask, encoder, correlate_row_g, offset, result, 1, xlatL2U, buckets_ptrs_g, pg);
				pb = UNCOMPRESS_ONE(channel_b, i, i_1, i_4, bpc_mask, encoder, correlate_row_b, offset, result, 2, xlatL2U, buckets_ptrs_b, pb);
				**/
			   
			   
				//this is inlined appendPixel
				resultData[pxCnt++] =
					(255   << 24) |    // alpha
					(pb << 16) |    // blue
					(pg <<  8) |    // green
					 pr;            // red
				cnt += 4;
				i_4 += 4;
			}
			if(!rle) {
				UPDATE_MODEL(stopidx, encoder, bpc, correlate_row_r, correlate_row_g, correlate_row_b);
				stopidx = i + (tabrand.call(wdi.JSQuic, rgb_state) & waitmask);
			} else {
				break;
			}
		}
	
		if(!rle) {
			i_4 = offset + i*4;
			for (; i < end; i++) {
				rle = RLE_PRED(i, encoder, i_4, currentOffset, run_index);
				if(rle) break;
				
				i_1 = i-1;
				

				////////////////////// INLINING UNCOMPRESS_ONE
				//r
				ret = golomb_decoding(buckets_ptrs_r[prevCorrelatedR].bestcode, encoder.io_word, bppmask);
				prevCorrelatedR = ret[0];
				codewordlen = ret[1];
				
				correlate_row_r[i] = prevCorrelatedR;

				pr = ((((xlatL2U[prevCorrelatedR] + 
					((pr + 
					result[i_4]) >>> 1)) 
					& bpc_mask
				)));

				eatbits.call(encoder, codewordlen);
				
				//g
				ret = golomb_decoding(buckets_ptrs_g[prevCorrelatedG].bestcode, encoder.io_word, bppmask);
				prevCorrelatedG = ret[0];
				codewordlen = ret[1];
				correlate_row_g[i] = prevCorrelatedG;

				pg = ((((xlatL2U[prevCorrelatedG] + 
					((pg + 
					result[i_4 + 1]) >>> 1)) 
					& bpc_mask
				)));

				eatbits.call(encoder, codewordlen);
				
				//b
				ret = golomb_decoding(buckets_ptrs_b[prevCorrelatedB].bestcode, encoder.io_word, bppmask);
				prevCorrelatedB = ret[0];
				codewordlen = ret[1];
				
				correlate_row_b[i] = prevCorrelatedB;

				pb = ((((xlatL2U[prevCorrelatedB] + 
					((pb + 
					result[i_4 + 2]) >>> 1)) 
					& bpc_mask
				)));

				eatbits.call(encoder, codewordlen);
				///////////////////// END INLINING
				
				/** 
				pr = UNCOMPRESS_ONE(channel_r, i, i_1, i_4, bpc_mask, encoder, correlate_row_r, offset, result, 0, xlatL2U, buckets_ptrs_r, pr);	
				pg = UNCOMPRESS_ONE(channel_g, i, i_1, i_4, bpc_mask, encoder, correlate_row_g, offset, result, 1, xlatL2U, buckets_ptrs_g, pg);
				pb = UNCOMPRESS_ONE(channel_b, i, i_1, i_4, bpc_mask, encoder, correlate_row_b, offset, result, 2, xlatL2U, buckets_ptrs_b, pb);
				**/
			   
				//this is inlined apendPixel
				resultData[pxCnt++] =
					(255   << 24) |    // alpha
					(pb << 16) |    // blue
					(pg <<  8) |    // green
					 pr;            // red
				cnt += 4;
				i_4 += 4;
			}
			if(!rle) {
				rgb_state.waitcnt = stopidx - end;
				encoder.cnt = cnt;
				encoder.pxCnt = pxCnt;
				return;
			}
		}
		
		//RLE
        rgb_state.waitcnt = stopidx - i;
        run_index = i;
        run_end = i + decode_run.call(wdi.JSQuic, encoder);
		
        for (; i < run_end; i++) {
			//this is inlined appendPixel
			resultData[pxCnt++] =
				(255 << 24) |    // alpha
				(pb << 16) |    // blue
				(pg <<  8) |    // green
				 pr;            // red
			cnt += 4;	
        }

        if (i === end) {
			encoder.cnt = cnt;
			encoder.pxCnt = pxCnt;
            return;
        }
	
		i_1 = i-1;
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
		pb =UNCOMPRESS_ONE_ROW0(channel_b, i, bpc_mask, encoder, correlate_row_b, pb);
		encoder.appendPixel(pr, pg, pb);
    }
    encoder.rgb_state.waitcnt = stopidx - end;
}

function UNCOMPRESS_ONE_0(channel, encoder, bpc_mask, offset) {
	var ret, codewordlen;
	channel.oldFirst = channel.correlate_row[0];
	ret = golomb_decoding(find_bucket(channel, 
		channel.correlate_row[0]).bestcode, encoder.io_word, wdi.JSQuic.bppmask);
	channel.correlate_row[0] = ret[0];
	codewordlen = ret[1];
	var residuum = wdi.xlatL2U[channel.correlate_row[0]];
	var prev = encoder.result[offset + channel.num_channel]; //PIXEL_B
	var resultpixel = ((residuum + prev) & bpc_mask);
	encoder.eatbits(codewordlen);
	return resultpixel;
} 

function UNCOMPRESS_ONE(channel, i, i_1, i_4, bpc_mask, encoder, correlate_row, offset, result, num_channel, xlatL2U, buckets_ptrs, prev_pixel) {
	var ret, codewordlen;
	ret = golomb_decoding(buckets_ptrs[correlate_row[i_1]].bestcode, encoder.io_word, wdi.JSQuic.bppmask);
	
	var data = ret[0];
	codewordlen = ret[1];
	correlate_row[i] = data;
	
	var ret = ((((xlatL2U[data] + 
		((prev_pixel + 
		result[offset + (i_4) + num_channel]) >>> 1)) 
		& bpc_mask
	)));
	
    encoder.eatbits(codewordlen);
	return ret;
}  


function UNCOMPRESS_ONE_ROW0_0(channel) {
	var ret, codewordlen;
	var encoder = channel.encoder;
	ret = golomb_decoding(find_bucket(channel, 0).bestcode, encoder.io_word, wdi.JSQuic.bppmask);
    channel.correlate_row[0] = ret[0]
	codewordlen = ret[1];
	var ret = wdi.xlatL2U[channel.correlate_row[0]];
    encoder.eatbits(codewordlen);
	return ret;
}  

function UNCOMPRESS_ONE_ROW0(channel, i, bpc_mask, encoder, correlate_row, prev_pixel) {
	var ret, codewordlen;
	ret = golomb_decoding(find_bucket(channel, correlate_row[i-1]).bestcode, encoder.io_word, wdi.JSQuic.bppmask);
	correlate_row[i] = ret[0];
	codewordlen = ret[1];
	var ret = CORELATE_0(encoder, channel, i, bpc_mask, correlate_row, prev_pixel);
    encoder.eatbits(codewordlen);
	return ret;
} 

function CORELATE_0(encoder, channel, curr, bpc_mask, correlate_row, prev_pixel) {
	return ((wdi.xlatL2U[correlate_row[curr]] + prev_pixel) & bpc_mask);
}
    
function PIXEL_A(encoder) {
	return encoder.result[encoder.cnt - 4];
}

function PIXEL_B(channel, encoder, pos, offset) {
	return encoder.result[offset + (pos*4) + channel.num_channel];
}