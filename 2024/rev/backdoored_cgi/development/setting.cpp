// License: LGPL

#include <unistd.h>
#include <iostream>
#include <stdexcept>

#include "cgicc/CgiDefs.h"
#include "cgicc/Cgicc.h"
#include "cgicc/HTTPHTMLHeader.h"
#include "cgicc/HTTPStatusHeader.h"
#include "cgicc/HTMLClasses.h"

using namespace std;
using namespace cgicc;

// TODO: google how to get output of command execution
// Used for connection test
void Ping(void) {
  execlp("ping", "-c5", "-w5", "8.8.8.8", NULL);
}

void ShowSettingPage(const Cgicc& cgi) {
  cout << HTTPHTMLHeader().setCookie(HTTPCookie("loggedin", "1"));
  cout << HTMLDoctype(HTMLDoctype::eStrict) << endl;
  cout << html() << endl;

  cout << head() << endl;
  cout << title() << "Setting" << title() << endl;
  cout << head() << endl;
  
  cout << body() << endl;
  cout << h1() << "C0mf0rt Router -- Setting" << h1() << endl;
  
  const CgiEnvironment& env = cgi.getEnvironment();
  
  cout << br() << endl;
  cout << "<p>TODO: implement settings</p>";

  cout << hr().set("class", "half") << endl;
  cout << cgicc::div().set("align", "center").set("class", "smaller") << endl;
  cout << "C0mf0rt Router" << endl;

  cout << cgicc::div() << endl;
  cout << body() << html() << endl;
}

void PrintForm(const Cgicc& cgi)
{
  cout << "<form method=\"post\" action=\"setting.cgi\">" << endl; 

  cout << "<table>" << endl;

  cout << "<tr><td class=\"title\">User</td>"
       << "<td class=\"form\">"
       << "<input type=\"text\" name=\"user\" />"
       << "</td></tr>" << endl;

  cout << "<tr><td class=\"title\">Password</td>"
       << "<td class=\"form\">"
       << "<input type=\"text\" name=\"password\" />"
       << "</td></tr>" << endl;

  cout << "</table>" << endl;

  cout << "<div class=\"center\"><p>"
       << "<input type=\"submit\" name=\"submit\" value=\"Login\" />"
       << "</p></div></form>" << endl;
}

void ShowLoginPage(const Cgicc& cgi, bool login_failed) {
    cout << HTTPHTMLHeader();
    cout << HTMLDoctype(HTMLDoctype::eStrict) << endl;
    cout << html() << endl;

    cout << head() << endl;
    cout << title() << "Login" << title() << endl;
    cout << head() << endl;
    
    cout << body() << endl;
    cout << h1() << "C0mf0rt Router -- Login" << h1() << endl;
    
    const CgiEnvironment& env = cgi.getEnvironment();
    
    if (login_failed) {
      cout << "<p style=\"color: red;\">Login failed.</p>";
    }

    PrintForm(cgi);

    cout << hr().set("class", "half") << endl;
    cout << cgicc::div().set("align", "center").set("class", "smaller") << endl;
    cout << "C0mf0rt Router" << endl;

    cout << cgicc::div() << endl;
    cout << body() << html() << endl;
}

void CgiMain(int argc, char *argv[]) {
  // For testing purpose: 
  //   throw an unhandled exception to make sure the server returns 500
  if (getenv("ENABLE_DEBUG_CGI") && argc >= 2 && std::string(argv[1]) == "500 test") {
    throw 1;
  }

  try {
    Cgicc cgi;
  
    for (const auto &cookie : cgi.getEnvironment().getCookieList()) {
      if (cookie.getName() != "loggedin") continue;

      if (cookie.getValue() == "1") {
        ShowSettingPage(cgi);
        return;
      }
    }

    const_form_iterator user = cgi.getElement("user");
    const_form_iterator password = cgi.getElement("password");
  
    bool login_failed = false;
    if (user != cgi.getElements().end() && password != cgi.getElements().end()) {
      if (user->getValue() == "admin" && password->getValue() == "admin") {
        ShowSettingPage(cgi);
        return;
      }

      login_failed = true;
    }

    ShowLoginPage(cgi, login_failed);
    return;
  } catch(const std::runtime_error& e) {
    cout << HTTPStatusHeader(502, "Error occurred.") << endl;
    return;
  } catch(const std::logic_error& e) {
    cout << HTTPStatusHeader(502, "Error occurred.") << endl;
    return;
  }
}

int main(int argc, char *argv[]) {
  CgiMain(argc, argv);
}

