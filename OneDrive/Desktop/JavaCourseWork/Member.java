// Member.java
// Represents a member who can purchase and cancel tickets
/**
 * this class have member who can buy and sell tickets
 */

import java.util.*;

public class Member {
    private String firstName;
    private String surname;
    private Map<String, Integer> purchasedTickets = new HashMap<>();

    /**
     * @see #Member(String, String)
     * constructor
     * @param firstName sets the first name of the member
     * @param surname   sets the last name of the member
     */

    public Member(String firstName, String surname) {
        this.firstName = firstName;
        this.surname = surname;
    }

    /**
     * @see #getFullName() getter method
     * @return returns the first and last name
     */

    public String getFullName() {
        return firstName + " " + surname;
    }

    /**
     * @see #buyTicket(Ticket, int)
     * this methods make sure user dont buy tickets for more then 3 shows
     * updates the purcahsed tickets
     * updated the qty
     */

    public void buyTicket(Ticket t, int qty) {
        String name = t.getName();
        //check is user already owns the tickect or own tickets for more then one show
        // both has to be true as we use and operator
        if (!purchasedTickets.containsKey(name) && purchasedTickets.size() >= 3) {
            System.out.println("❌ " + getFullName() + " already holds 3 types of tickets.");
            return;
        }

        // checks how many tickects does the user own. used default value to avoid null cases
        int owned = purchasedTickets.getOrDefault(name, 0);
        //adding the current purchased ticket to new total current + previous
        purchasedTickets.put(name, owned + qty);
        // updating the available tickets
        t.setAvailable(t.getAvailable() - qty);
        System.out.println("✅ " + getFullName() + " bought " + qty + " ticket(s) for " + name);
    }

    /**
     * @see #cancelTicket(Ticket, int)
     * check if member already owns the ticket
     * removes the cancelled ticket from the map
     *  add ticket bact to qty
     */

    public void cancelTicket(Ticket t, int qty) {
        String name = t.getName();
        //check if the user owns the ticket
        if (!purchasedTickets.containsKey(name)) {
            System.out.println("❌ " + getFullName() + " does not own any " + name + " tickets.");
            return;
        }

        int owned = purchasedTickets.get(name);
        // if the user purchase more then available ticket removes ticket type completely from the list
        if (qty >= owned) {
            purchasedTickets.remove(name);
        } else {
            // removes the ticket from own
            purchasedTickets.put(name, owned - qty);
        }

        // updating the quantity
        t.setAvailable(t.getAvailable() + qty);
        System.out.println("↩️ " + getFullName() + " cancelled " + qty + " ticket(s) for " + name);
    }

    /**
     * calculate the total cost user spent on tickets
     *
     */

    public double getTotalCost(Map<String, Ticket> ticketLookup) {
        double total = 0;
        for (Map.Entry<String, Integer> e : purchasedTickets.entrySet()) {
            Ticket t = ticketLookup.get(e.getKey());
            if (t != null)
                total += e.getValue() * t.getPrice();
        }
        return total;
    }


    /**
     *this method displays the members and the number of tickets they own and also tho total spen
     */

    public void display(Map<String, Ticket> ticketLookup) {
        System.out.println("Member: " + getFullName());
        if (purchasedTickets.isEmpty()) {
            // member bought nothing prints
            System.out.println("  No tickets purchased.");
            return;
        }
        double totalAll = 0;
        //loops and prints every ticket they bought
        for (Map.Entry<String, Integer> e : purchasedTickets.entrySet()) {
            String ticketName = e.getKey();
            int qty = e.getValue();
            Ticket t = ticketLookup.get(ticketName);
            //add the price of the tickets to the subtotal
            double subtotal = qty * (t != null ? t.getPrice() : 0);
            totalAll += subtotal;
            System.out.printf("  %-35s | Qty: %-3d | Subtotal: £%.2f%n", ticketName, qty, subtotal);
        }
        System.out.printf("  Total spent: £%.2f%n", totalAll);
    }
}
