#include <iostream>

struct Node {
    int data;
    Node* next;
};

Node* head = NULL;

// Function to insert a new node at the front of the list
void push(int new_data) {
    Node* new_node = new Node();
    new_node->data = new_data;
    new_node->next = head;
    head = new_node;
}

// Function to reverse the linked list
void reverse() {
    Node* current = head;
    Node* prev = NULL;
    Node* next = NULL;

    while (current != NULL) {
        next = current->next;
        current->next = prev;
        prev = current;
        current = next;
    }

    head = prev;
}

// Function to print the linked list
void printList() {
    Node* temp = head;
    while (temp != NULL) {
        std::cout << temp->data << " ";
        temp = temp->next;
    }
    std::cout << std::endl;
}

int main() {
    push(5);
    push(4);
    push(3);
    push(2);
    push(1);

    std::cout << "Original List: ";
    printList();

    reverse();

    std::cout << "Reversed List: ";
    printList();

    return 0;
}
