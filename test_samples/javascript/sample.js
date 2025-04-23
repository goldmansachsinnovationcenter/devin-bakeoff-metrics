/**
 * Sample JavaScript file for testing the JavaScript analyzer.
 */

function calculateComplexValue(a, b, c, d, e) {
  let result = 0;
  
  if (a > 10) {
    if (b > 20) {
      if (c > 30) {
        if (d > 40) {
          if (e > 50) {
            result = a * b * c * d * e;
          } else {
            result = a * b * c * d;
          }
        } else {
          result = a * b * c;
        }
      } else {
        result = a * b;
      }
    } else {
      result = a;
    }
  }
  
  return result;
}

function processUserData(userData) {
  eval("var result = " + userData);  // Security issue: eval with user input
  return result;
}

var unused_variable = "This variable is never used";

module.exports = {
  calculateComplexValue,
  processUserData
};
