kimchi.report_add_main = function() {
    var addReportForm = $('#form-report-add');
    var submitButton = $('#button-report-add');
    var nameTextbox = $('input[name="name"]', addReportForm);
    var errorMessage = $('#report-error-message');
    var submitForm = function(event) {
        if(submitButton.prop('disabled')) {
            return false;
        }
        var reportName = nameTextbox.val();
        var validator = RegExp("^[A-Za-z0-9-]*$");
        if (!validator.test(reportName)) {
            errorMessage.text(i18n['KCHDR6011M']);
            return false;
        }
        var formData = addReportForm.serializeObject();
        errorMessage.text('');
        submitButton
            .text(i18n['KCHDR6007M'])
            .prop('disabled', true);
        nameTextbox.prop('disabled', true);
        kimchi.createReport(formData, function(result) {
            kimchi.window.close();
            kimchi.topic('kimchi/debugReportAdded').publish({
                result: result
            });
        }, function(result) {
            if (result['reason']) {
                var errText = result['reason'];
            }
            else {
                var errText = result['responseJSON']['reason'];
            }
            result && $('#report-error-message').text(errText);
            submitButton
                .text(i18n['KCHDR6006M'])
                .prop('disabled', false);
            nameTextbox.prop('disabled', false).focus();
        });

        event.preventDefault();
    };

    addReportForm.on('submit', submitForm);
    submitButton.on('click', submitForm);
};
