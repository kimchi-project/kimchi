Project Burnet i18n
===================

This file is a guide for Burnet i18n.

Please follow these steps.

1. Edit your source code.

    Please put the message that needs to be translated in the\_().

    Such as: `_("Hello, Burnet")`

2. make portable object files with .po suffix.

    Update available po files

    $ python setup.py make\_po

    Generate new po files

    $ python setup.py make\_po --lang zh\_CN,en\_US

3. Show all available po files information.

    $ python setup.py info\_po

4. Open the po file, and add translation to your message.

5. Compile machine object files with .mo suffix:

    $ python setup.py make\_mo

6. Restart burnet project
