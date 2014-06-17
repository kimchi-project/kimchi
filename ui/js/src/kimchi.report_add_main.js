/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2014
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
kimchi.report_add_main = function() {
    var reportGridID = 'available-reports-grid';
    var generateButton = $('#' + reportGridID + '-generate-button');
    var addReportForm = $('#form-report-add');
    var submitButton = $('#button-report-add');
    var nameTextbox = $('input[name="name"]', addReportForm);
    nameTextbox.select();

    /*
     * FIXME:
     *   Currently, all buttons will be disabled when a report is being
     * generated. Though operations on existing debug reports shouldn't
     * be affected when a new one is being generated, and it's expected
     * to enable Rename/Remove/Download Buttons whenever users click an
     * existing report row in the grid.
     */
    var disableToolbarButtons = function(event, toEnable) {
        $('#' + reportGridID + ' .grid-toolbar button')
            .prop('disabled', !toEnable);
    };

    var submitForm = function(event) {
        if(submitButton.prop('disabled')) {
            return false;
        }
        var reportName = nameTextbox.val();
        var validator = RegExp("^[A-Za-z0-9-]*$");
        if (!validator.test(reportName)) {
            kimchi.message.error.code('KCHDR6011M');
            return false;
        }
        var formData = addReportForm.serializeObject();
        var taskAccepted = false;
        disableToolbarButtons();
        submitButton.prop('disabled', true);
        $('.grid-body table tr', '#' + reportGridID)
            .on('click', disableToolbarButtons);
        kimchi.createReport(formData, function(result) {
            $('.grid-body-view table tr:first-child', '#' + reportGridID).remove();
            $('.grid-body table tr', '#' + reportGridID)
                .off('click', disableToolbarButtons);
            generateButton.prop('disabled', false);
            kimchi.topic('kimchi/debugReportAdded').publish({
                result: result
            });
        }, function(result) {
            // Error message from Async Task status
            if (result['message']) {
                var errText = result['message'];
            }
            // Error message from standard kimchi exception
            else {
                var errText = result['responseJSON']['reason'];
            }
            result && kimchi.message.error(errText);
            taskAccepted &&
                $('.grid-body-view table tr:first-child',
                    '#' + reportGridID).remove();
            $('.grid-body table tr', '#' + reportGridID)
                .off('click', disableToolbarButtons);
            generateButton.prop('disabled', false);
            submitButton.prop('disabled', false);
            nameTextbox.select();
        }, function(result) {
            if(taskAccepted) {
                return;
            }
            taskAccepted = true;
            kimchi.window.close();
            var reportName = nameTextbox.val() || i18n['KCHDR6012M'];
            $('.grid-body-view table tbody', '#' + reportGridID).prepend(
                '<tr>' +
                    '<td>' +
                        '<div class="cell-text-wrapper">' + reportName + '</div>' +
                    '</td>' +
                    '<td id ="id-debug-img">' +
                        '<div class="cell-text-wrapper">' + i18n['KCHDR6007M'] + '</div>' +
                    '</td>' +
                '</tr>'
            );
        });

        event.preventDefault();
    };

    addReportForm.on('submit', submitForm);
    submitButton.on('click', submitForm);
};
