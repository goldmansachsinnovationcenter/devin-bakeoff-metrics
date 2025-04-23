/**
 * Sample Java file for testing the Java analyzer.
 */
public class Sample {
    
    public int calculateComplexValue(int a, int b, int c, int d, int e) {
        int result = 0;
        
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
    
    public void processUserInput(String userInput) {
        try {
            Runtime.getRuntime().exec(userInput);
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
    
    private String unusedVariable = "This variable is never used";
    
    public static void main(String[] args) {
        Sample sample = new Sample();
        int result = sample.calculateComplexValue(15, 25, 35, 45, 55);
        System.out.println("Result: " + result);
        
        if (args.length > 0) {
            sample.processUserInput(args[0]);
        }
    }
}
