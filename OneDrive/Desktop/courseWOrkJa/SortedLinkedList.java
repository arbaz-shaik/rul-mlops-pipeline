// SortedLinkedList.java
// A generic sorted linked list using Comparable<E>

public class SortedLinkedList<E extends Comparable<E>> {
    private Node<E> head;

    private static class Node<E> {
        E data;
        Node<E> next;
        Node(E data) { this.data = data; }
    }

    public void insert(E value) {
        Node<E> newNode = new Node<>(value);
        if (head == null || head.data.compareTo(value) > 0) {
            newNode.next = head;
            head = newNode;
            return;
        }

        Node<E> current = head;
        while (current.next != null && current.next.data.compareTo(value) < 0) {
            current = current.next;
        }
        newNode.next = current.next;
        current.next = newNode;
    }

    public void display() {
        Node<E> current = head;
        while (current != null) {
            System.out.println(current.data);
            current = current.next;
        }
    }

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
