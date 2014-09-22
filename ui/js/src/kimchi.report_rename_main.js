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
kimchi.report_rename_main = function() {
    var renameReportForm = $('#form-report-rename');
    var submitButton = $('#button-report-rename');
    var nameTextbox = $('input[name="name"]', renameReportForm);
    var submitForm = function(event) {
        if(submitButton.prop('disabled')) {
            return false;
        }
        var reportName = nameTextbox.val();

        // if the user hasn't changed the report's name,
        // nothing should be done.
        if (reportName == kimchi.selectedReport) {
            kimchi.message.error.code('KCHDR6013M');
            return false;
        }

        var validator = RegExp("^[A-Za-z0-9-]*$");
        if (!validator.test(reportName)) {
            kimchi.message.error.code('KCHDR6011M');
            return false;
        }
        var formData = renameReportForm.serializeObject();
        submitButton.prop('disabled', true);
        nameTextbox.prop('disabled', true);
        kimchi.renameReport(kimchi.selectedReport, formData, function(result) {
            submitButton.prop('disabled', false);
            nameTextbox.prop('disabled', false);
            kimchi.window.close();
            kimchi.topic('kimchi/debugReportRenamed').publish({
                result: result
            });
        }, function(result) {
            var errText = result &&
                result['responseJSON'] &&
                result['responseJSON']['reason'];
            kimchi.message.error(errText);
            submitButton.prop('disabled', false);
            nameTextbox.prop('disabled', false).focus();
        });

        event.preventDefault();
    };

    renameReportForm.on('submit', submitForm);
    submitButton.on('click', submitForm);

    nameTextbox.val(kimchi.selectedReport).select();
};
