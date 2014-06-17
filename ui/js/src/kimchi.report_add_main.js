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
    var addReportForm = $('#form-report-add');
    var submitButton = $('#button-report-add');
    var nameTextbox = $('input[name="name"]', addReportForm);
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
        kimchi.window.close();
        $('#' + reportGridID + '-generate-button').prop('disabled',true);
        $('#' + reportGridID + '-remove-button').prop('disabled',true);
        $('#' + reportGridID + '-download-button').prop('disabled',true);
        $('#' + reportGridID + '-rename-button').prop('disabled',true);
        $('.grid-body table tr', '#' + reportGridID).click(function() {
            $('#' + reportGridID + '-remove-button').prop('disabled',true);
            $('#' + reportGridID + '-download-button').prop('disabled',true);
            $('#' + reportGridID + '-rename-button').prop('disabled',true);
        });
        var textboxValue = $('#report-name-textbox').val();
        if (textboxValue != "") {
            $('.grid-body-view table', '#' + reportGridID).prepend(
                '<tr>' +
                    '<td>' +
                        '<div class="cell-text-wrapper">' + textboxValue + '</div>' +
                    '</td>' +
                    '<td id ="id-debug-img">' +
                        '<div class="cell-text-wrapper">' + i18n['KCHDR6007M'] + '</div>' +
                    '</td>' +
                '</tr>'
            );
        }
        else {
            $('.grid-body-view table', '#' + reportGridID).prepend(
                '<tr>' +
                    '<td>' +
                        '<div class="cell-text-wrapper">' + i18n['KCHDR6012M'] + '</div>' +
                    '</td>' +
                    '<td id ="id-debug-img">' +
                        '<div class="cell-text-wrapper">' + i18n['KCHDR6007M'] + '</div>' +
                    '</td>' +
                '</tr>'
            );
        }
        kimchi.createReport(formData, function(result) {
            $('.grid-body-view table tr:first-child', '#' + reportGridID).remove();
            $('#' + reportGridID + '-generate-button').prop('disabled',false);
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
            result && kimchi.message.error(errText)
            $('.grid-body-view table tr:first-child', '#' + reportGridID).remove();
        });

        event.preventDefault();
    };

    addReportForm.on('submit', submitForm);
    submitButton.on('click', submitForm);
};
