/*
 * Project Burnet
 *
 * Copyright IBM, Corp. 2013
 *
 * Authors:
 *  Hongliang Wang <hlwanghl@cn.ibm.com>
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
burnet.popable = function() {
	$(document).click(function(e) {
		$('.popable').removeClass('open');
	});
	$(document).on("click", ".popable", function(e) {
		var isOpen = $(this).hasClass('open');
		$(".popable").removeClass('open');
		if (!isOpen) {
			$(this).addClass('open');
		}
		e.preventDefault();
		e.stopPropagation();
	});
};
