def delete_customer(db: Session, customer_id: int) -> bool:
    """Delete a customer by ID"""
    try:
        # Get the customer
        customer = get_customer(db, customer_id)
        
        if not customer:
            print(f"Customer with ID {customer_id} not found")
            return False
        
        # Delete the customer
        db.delete(customer)
        db.commit()
        
        print(f"Customer with ID {customer_id} deleted successfully")
        return True
    except Exception as e:
        db.rollback()
        print(f"Error deleting customer: {e}")
        import traceback
        traceback.print_exc()
        return False