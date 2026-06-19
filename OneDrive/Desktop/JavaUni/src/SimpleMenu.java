import java.nio.channels.Selector;
import  java.util.Scanner;

public class SimpleMenu {

    Scanner scan = new Scanner(System.in);

    public static void main(String[] args) {

        SimpleMenu smenu = new SimpleMenu();
        boolean a = true;
        while (a) {
            smenu.menu();
            smenu.select();
        }  //never use same name twice in objects


    }

    public void menu() {

        System.out.println("Welcome to Simple Menu");
        System.out.println();
        System.out.println("---- Menu ----");
        System.out.println("1. Chicken Biryani - £8.99");
        System.out.println("2. Paneer Butter Masala - £7.49");
        System.out.println("3. Masala Dosa - £6.99");
        System.out.println("4. Grilled Fish - £9.50");
        System.out.println("5. Gulab Jamun (Dessert) - £3.99");
        System.out.println("Please enter your choice by entering number of it");

    }

    public void select() {
        int choice = scan.nextInt();
        switch (choice) {
            case 1:
                System.out.println("You selected Chicken Biryani. Price: £8.99");
                break;
            case 2:
                System.out.println("You selected Paneer Butter Masala. Price: £7.49");
                break;
            case 3:
                System.out.println("You selected Masala Dosa. Price: £6.99");
                break;
            case 4:
                System.out.println("You selected Grilled Fish. Price: £9.50");
                break;
            case 5:
                System.out.println("You selected Gulab Jamun. Price: £3.99");
                break;
            default:
                System.out.println("Invalid choice. Please select a number between 1 and 5.");
        }

    }

}


