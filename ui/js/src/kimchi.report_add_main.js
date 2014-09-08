/*
 * Project Kimchi
 *
 * Copyright IBM, Corp. 2013-2014
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
    nameTextbox.select();

    var submitForm = function(event) {
        if(submitButton.prop('disabled')) {
            return false;
        }
        var reportName = nameTextbox.val();
        var validator = RegExp("^[_A-Za-z0-9-]*$");
        if (!validator.test(reportName)) {
            kimchi.message.error.code('KCHDR6011M');
            return false;
        }
        var formData = addReportForm.serializeObject();
        var taskAccepted = false;
        var onTaskAccepted = function() {
            if(taskAccepted) {
                return;
            }
            taskAccepted = true;
            kimchi.window.close();
            kimchi.topic('kimchi/debugReportAdded').publish();
        };

        kimchi.createReport(formData, function(result) {
            onTaskAccepted();
            kimchi.topic('kimchi/debugReportAdded').publish();
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
            submitButton.prop('disabled', false);
            nameTextbox.select();
        }, onTaskAccepted);

        event.preventDefault();
    };

    addReportForm.on('submit', submitForm);
    submitButton.on('click', submitForm);
};
