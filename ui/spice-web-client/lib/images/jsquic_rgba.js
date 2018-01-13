function QUIC_UNCOMPRESS_RGBA(encoder, channels, bpc, type) {
	quic_uncompress_row0(encoder, channels, bpc, type);
	quic_four_uncompress_row0(encoder, encoder.channels[3], bpc, type);
	encoder.row_completed();
	var height = encoder.height;
	var rgb_state = encoder.rgb_state;
	for (var row = 1; row < height; row++) {
		quic_uncompress_row(encoder, channels, bpc, type, rgb_state);
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

	var offset = ((encoder.rows_completed-1) * computedWidth);
	
	var data;
	
	var eatbits = encoder.eatbits;
	var appendAlpha = encoder.appendAlpha;
	
	var alpha;
	
	var ret, codewordlen;
	var bppmask = wdi.JSQuic.bppmask;
	
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
		alpha = encoder.result[encoder.alphaPos-4];
    }
	
	for(;;) {
		while (stopidx < end) {
			for (; i <= stopidx; i++) {
				rle = RLE_PRED_A(i, encoder, run_index, computedWidth, rows_completed);
				if(rle) break;

				ret = golomb_decoding(find_bucket(channel, correlate_row[i-1]).bestcode, 
				encoder.io_word, bppmask);
				
				data = ret[0];
				codewordlen = ret[1];
		
				correlate_row[i] = data;
				alpha = (((wdi.xlatL2U[data] + 
					((alpha + PIXEL_B(channel, encoder, i, offset)) >>> 1)) & bpc_mask) >>> 0);
	
				appendAlpha.call(encoder, alpha);
				eatbits.call(encoder, codewordlen);
			}
			if(!rle) {
				real_update_model(channel.state, find_bucket(channel, 
					correlate_row[stopidx-1]), correlate_row[stopidx], bpc);
				stopidx = i + (wdi.JSQuic.tabrand(channel.state) & waitmask);
			} else {
				break;
			}
		}
		if(!rle) {
			for (; i < end; i++) {
				rle = RLE_PRED_A(i, encoder, run_index, computedWidth, rows_completed);
				if(rle) break;
				
				ret = golomb_decoding(find_bucket(channel, correlate_row[i-1]).bestcode, 
				encoder.io_word, bppmask);
		
				data = ret[0];
				codewordlen = ret[1];
				correlate_row[i] = data;
				alpha = (((wdi.xlatL2U[data] + 
					((alpha + PIXEL_B(channel, encoder, i, offset)) >>> 1)) & bpc_mask) >>> 0);
	
				appendAlpha.call(encoder, alpha);
				eatbits.call(encoder, codewordlen);
			}
			if(!rle) {
				channel.state.waitcnt = stopidx - end;
				return;
			}
		}
		
		//RLE
        channel.state.waitcnt = stopidx - i;
        run_index = i;
        run_end = i + wdi.JSQuic.decode_channel_run(encoder, channel);

		var cpos = ((encoder.rows_completed) * (encoder.width*4)) + (i*4);
		var a = encoder.result[cpos-1];
		
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
			correlate_row[stopidx-1]), correlate_row[stopidx], bpc);
        stopidx = i + (wdi.JSQuic.tabrand(channel.state) & waitmask);
    }

    for (; i < end; i++) {
        UNCOMPRESS_ONE_ROW0_A(channel, i, bpc_mask, encoder, correlate_row);
    }
    channel.state.waitcnt = stopidx - end;
}

function SAME_PIXEL_A(i, result) {
	if(result[i-1] === result[i+3]) {
		return true;
	}
	return false;
}

function RLE_PRED_A(i, encoder, run_index, width, rows_completed) {
	var pr = ((rows_completed-1) * width) + (i*4); //prev r
	if(run_index !== i && i > 2) {
		if(SAME_PIXEL_A(pr, encoder.result)) {
			pr = ((rows_completed) * width) + ((i-1)*4); // cur r
			if(SAME_PIXEL_A(pr, encoder.result)) {
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
		channel.correlate_row[-1]).bestcode, encoder.io_word, wdi.JSQuic.bppmask);
	channel.correlate_row[0] = ret[0];
	codewordlen = ret[1];
	var residuum = wdi.xlatL2U[channel.correlate_row[0]];
	var prev = PIXEL_B(channel, encoder, 0, offset);
	var resultpixel = ((residuum + prev) & bpc_mask) >>> 0;
	encoder.appendAlpha(resultpixel);
	encoder.eatbits(codewordlen);
	return resultpixel;
} 

function UNCOMPRESS_ONE_A(channel, i, bpc_mask, encoder, correlate_row, offset) {
	var ret, codewordlen;
	ret = golomb_decoding(find_bucket(channel, correlate_row[i-1]).bestcode, 
		encoder.io_word, wdi.JSQuic.bppmask);
	var data = ret[0];
	codewordlen = ret[1];
	correlate_row[i] = data;
    encoder.appendAlpha((((wdi.xlatL2U[data] + 
		((PIXEL_A_A(encoder) + PIXEL_B(channel, encoder, i, offset)) >>> 1)) & bpc_mask) >>> 0));
	
    encoder.eatbits(codewordlen);
}  


function UNCOMPRESS_ONE_ROW0_0_A(channel) {
	var ret, codewordlen;
	var encoder = channel.encoder;
	ret = golomb_decoding(find_bucket(channel, 0).bestcode, encoder.io_word, wdi.JSQuic.bppmask);
	channel.correlate_row[0] = ret[0];
	codewordlen = ret[1];
    encoder.appendAlpha(wdi.xlatL2U[channel.correlate_row[0]]);
    encoder.eatbits(codewordlen);
}  

function UNCOMPRESS_ONE_ROW0_A(channel, i, bpc_mask, encoder, correlate_row) {
	var ret, codewordlen;
	ret = golomb_decoding(find_bucket(channel, correlate_row[i-1]).bestcode, encoder.io_word, wdi.JSQuic.bppmask);
	var data = ret[0];
	codewordlen = ret[1];
	correlate_row[i] = data;
	encoder.appendAlpha(CORELATE_0_A(encoder, channel, i, bpc_mask, correlate_row));
    encoder.eatbits(codewordlen);
}  

function CORELATE_0_A(encoder, channel, curr, bpc_mask, correlate_row) {
	return ((wdi.xlatL2U[correlate_row[curr]] + PIXEL_A_A(encoder)) & bpc_mask) >>> 0;
}

function PIXEL_A_A(encoder) {
	return encoder.result[encoder.alphaPos - 4];
}