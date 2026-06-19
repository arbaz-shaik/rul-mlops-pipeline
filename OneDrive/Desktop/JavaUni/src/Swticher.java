import  java.util.Scanner;
public class Swticher {
    public static void main(String[] args) {

        Scanner input = new Scanner(System.in);
        boolean done = false;
        while(!done){
            System.out.println("Enter a Option");
            int option = input.nextInt();
            switch (option){
                case 1:
                case 2:
                        System.out.println("you enter 1 or 2");
                        break;
                case 3:
                System.out.println("Goodbbye");
                done = true;
                break;
                default :
                    System.out.println("Invalid Option");

            }
        }


    }
}