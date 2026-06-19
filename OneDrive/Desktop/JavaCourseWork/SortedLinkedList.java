// SortedLinkedList.java
// A generic sorted linked list using Comparable<E>

/**
 * sorted list data with type parametet <E>
 * @param <E>
 */

public class SortedLinkedList<E extends Comparable<E>> {
    private Node<E> head;// first node

    // this NOde store the data and links it with the next Node
    private static class Node<E> {
        E data;
        Node<E> next;
        Node(E data) { this.data = data; }
    }


    //insert value in the list and also maintain the list sorted
    public void insert(E value) {
        Node<E> newNode = new Node<>(value);
        if (head == null || head.data.compareTo(value) > 0) {
            newNode.next = head;
            head = newNode;
            return;
        }

        // the list should be empty or the new value should be at the start
        Node<E> current = head;
        while (current.next != null && current.next.data.compareTo(value) < 0) {
            current = current.next;
        }
        newNode.next = current.next;
        current.next = newNode;
    }

    //displays all element in the list
    public void display() {
        Node<E> current = head;
        while (current != null) {
            System.out.println(current.data);
            current = current.next;
        }
    }
   // compare each element and return value if found or returns null
    public E find(E value) {
        Node<E> current = head;
        while (current != null) {
            if (current.data.equals(value))
                return current.data;
            current = current.next;
        }
        return null;
    }
}
