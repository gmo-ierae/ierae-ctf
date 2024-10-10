FROM httpd:latest

RUN rm /usr/local/apache2/cgi-bin/*

COPY flag /flag
COPY httpd.conf /usr/local/apache2/conf/httpd.conf
COPY patched_setting.cgi /usr/local/apache2/cgi-bin/setting.cgi

RUN chown root:www-data /usr/local/apache2/htdocs/
RUN chmod 775 /usr/local/apache2/htdocs/

RUN chown root:root /usr/local/apache2/conf/httpd.conf /usr/local/apache2/cgi-bin/setting.cgi /flag
RUN chmod 755 /usr/local/apache2/conf/httpd.conf /usr/local/apache2/cgi-bin/setting.cgi /flag
RUN mv /flag /flag-$(md5sum /flag | awk '{print $1}')
