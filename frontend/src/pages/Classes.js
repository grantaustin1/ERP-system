import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Textarea } from '../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '../components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from '../components/ui/command';
import { Popover, PopoverContent, PopoverTrigger } from '../components/ui/popover';
import { Calendar, Clock, Users, Plus, Edit, Trash2, UserCheck, Check, ChevronsUpDown } from 'lucide-react';

const DAYS_OF_WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];
const CLASS_TYPES = ['Yoga', 'Pilates', 'Spin', 'CrossFit', 'Boxing', 'HIIT', 'Zumba', 'Bootcamp', 'Strength Training', 'Cardio'];

function Classes() {
  const [classes, setClasses] = useState([]);
  const [bookings, setBookings] = useState([]);
  const [members, setMembers] = useState([]);
  const [membershipTypes, setMembershipTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showClassDialog, setShowClassDialog] = useState(false);
  const [showBookingDialog, setShowBookingDialog] = useState(false);
  const [editingClass, setEditingClass] = useState(null);
  const [selectedClass, setSelectedClass] = useState(null);
  const [activeTab, setActiveTab] = useState('schedule');

  const [classForm, setClassForm] = useState({
    name: '',
    description: '',
    class_type: '',
    instructor_name: '',
    duration_minutes: 60,
    capacity: 20,
    day_of_week: '',
    start_time: '',
    end_time: '',
    is_recurring: true,
    class_date: '',
    room: '',
    allow_waitlist: true,
    waitlist_capacity: 10,
    booking_window_days: 7,
    cancel_window_hours: 2,
    drop_in_price: 0,
    membership_types_allowed: []
  });

  const [bookingForm, setBookingForm] = useState({
    class_id: '',
    member_id: '',
    booking_date: '',
    notes: ''
  });

  const [memberSearchOpen, setMemberSearchOpen] = useState(false);
  
  // Separate date/time fields for auto-advance
  const [dateFields, setDateFields] = useState({
    year: '',
    month: '',
    day: '',
    hour: '',
    minute: ''
  });

  // Refs for auto-advancing between fields
  const yearRef = useRef(null);
  const monthRef = useRef(null);
  const dayRef = useRef(null);
  const hourRef = useRef(null);
  const minuteRef = useRef(null);

  // Use localhost backend when frontend is on localhost, otherwise use env variable
  const API_URL = window.location.hostname === 'localhost' 
    ? 'http://localhost:8001' 
    : process.env.REACT_APP_BACKEND_URL;

  // Auto-advance handler for date/time fields
  const handleDateFieldChange = (field, value, maxLength, nextRef) => {
    // Only allow numbers
    const numericValue = value.replace(/\D/g, '');
    
    // Update the field with limited length
    const limitedValue = numericValue.slice(0, maxLength);
    setDateFields(prev => ({ ...prev, [field]: limitedValue }));
    
    // Auto-advance to next field when current field is filled
    if (limitedValue.length === maxLength && nextRef && nextRef.current) {
      nextRef.current.focus();
    }
  };

  // Combine date fields into datetime-local format (YYYY-MM-DDTHH:MM)
  useEffect(() => {
    const { year, month, day, hour, minute } = dateFields;
    if (year.length === 4 && month.length === 2 && day.length === 2 && hour.length === 2 && minute.length === 2) {
      const dateTimeString = `${year}-${month}-${day}T${hour}:${minute}`;
      setBookingForm(prev => ({ ...prev, booking_date: dateTimeString }));
    }
  }, [dateFields]);

  useEffect(() => {
    fetchClasses();
    fetchBookings();
    fetchMembers();
    fetchMembershipTypes();
  }, []);

  const fetchClasses = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/classes`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setClasses(data);
      }
    } catch (error) {
      console.error('Failed to fetch classes:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchBookings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/bookings`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setBookings(data);
      }
    } catch (error) {
      console.error('Failed to fetch bookings:', error);
    }
  };

  const fetchMembers = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/members`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setMembers(data);
      }
    } catch (error) {
      console.error('Failed to fetch members:', error);
    }
  };

  const fetchMembershipTypes = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/membership-types`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setMembershipTypes(data);
      }
    } catch (error) {
      console.error('Failed to fetch membership types:', error);
    }
  };

  const handleCreateClass = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/classes`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(classForm)
      });

      if (response.ok) {
        await fetchClasses();
        setShowClassDialog(false);
        resetClassForm();
        alert('Class created successfully!');
      } else {
        const error = await response.json();
        alert(`Failed to create class: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error creating class:', error);
      alert('Failed to create class');
    }
  };

  const handleUpdateClass = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/classes/${editingClass.id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(classForm)
      });

      if (response.ok) {
        await fetchClasses();
        setShowClassDialog(false);
        setEditingClass(null);
        resetClassForm();
        alert('Class updated successfully!');
      } else {
        const error = await response.json();
        alert(`Failed to update class: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error updating class:', error);
      alert('Failed to update class');
    }
  };

  const handleDeleteClass = async (classId) => {
    if (!window.confirm('Are you sure you want to delete this class?')) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/classes/${classId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        await fetchClasses();
        alert('Class deleted successfully!');
      } else {
        alert('Failed to delete class');
      }
    } catch (error) {
      console.error('Error deleting class:', error);
      alert('Failed to delete class');
    }
  };

  const handleCreateBooking = async (e) => {
    e.preventDefault();
    
    // Debug: Log the booking form data
    console.log('Submitting booking:', bookingForm);
    console.log('Date fields:', dateFields);
    
    // Validate booking_date is present
    if (!bookingForm.booking_date) {
      alert('Please fill in all date and time fields');
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/bookings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        credentials: 'include',
        mode: 'cors',
        body: JSON.stringify(bookingForm)
      });

      if (response.ok) {
        await fetchBookings();
        setShowBookingDialog(false);
        resetBookingForm();
        alert('Booking created successfully!');
      } else {
        const error = await response.json();
        alert(`Failed to create booking: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error creating booking:', error);
      alert(`Failed to create booking: ${error.message}`);
    }
  };

  const handleCheckIn = async (bookingId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/bookings/${bookingId}/check-in`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        await fetchBookings();
        alert('Member checked in successfully!');
      } else {
        const error = await response.json();
        alert(`Failed to check in: ${error.detail}`);
      }
    } catch (error) {
      console.error('Error checking in:', error);
      alert('Failed to check in');
    }
  };

  const handleCancelBooking = async (bookingId) => {
    if (!window.confirm('Are you sure you want to cancel this booking?')) return;

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/bookings/${bookingId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ status: 'cancelled', cancellation_reason: 'Cancelled by admin' })
      });

      if (response.ok) {
        await fetchBookings();
        alert('Booking cancelled successfully!');
      } else {
        alert('Failed to cancel booking');
      }
    } catch (error) {
      console.error('Error cancelling booking:', error);
      alert('Failed to cancel booking');
    }
  };

  const resetClassForm = () => {
    setClassForm({
      name: '',
      description: '',
      class_type: '',
      instructor_name: '',
      duration_minutes: 60,
      capacity: 20,
      day_of_week: '',
      start_time: '',
      end_time: '',
      is_recurring: true,
      class_date: '',
      room: '',
      allow_waitlist: true,
      waitlist_capacity: 10,
      booking_window_days: 7,
      cancel_window_hours: 2,
      drop_in_price: 0,
      membership_types_allowed: []
    });
  };

  const resetBookingForm = () => {
    setBookingForm({
      class_id: '',
      member_id: '',
      booking_date: '',
      notes: ''
    });
    setDateFields({
      year: '',
      month: '',
      day: '',
      hour: '',
      minute: ''
    });
    setMemberSearchOpen(false);
  };

  const openEditDialog = (classItem) => {
    setEditingClass(classItem);
    setClassForm({
      name: classItem.name,
      description: classItem.description || '',
      class_type: classItem.class_type,
      instructor_name: classItem.instructor_name || '',
      duration_minutes: classItem.duration_minutes,
      capacity: classItem.capacity,
      day_of_week: classItem.day_of_week || '',
      start_time: classItem.start_time,
      end_time: classItem.end_time,
      is_recurring: classItem.is_recurring,
      class_date: classItem.class_date || '',
      room: classItem.room || '',
      allow_waitlist: classItem.allow_waitlist,
      waitlist_capacity: classItem.waitlist_capacity,
      booking_window_days: classItem.booking_window_days,
      cancel_window_hours: classItem.cancel_window_hours,
      drop_in_price: classItem.drop_in_price,
      membership_types_allowed: classItem.membership_types_allowed || []
    });
    setShowClassDialog(true);
  };

  const openBookingDialog = (classItem) => {
    setSelectedClass(classItem);
    
    let targetDate;
    
    // Calculate the next available date/time for this class
    if (classItem.class_date) {
      // One-time class - use the specific date
      targetDate = new Date(classItem.class_date);
    } else if (classItem.is_recurring && classItem.day_of_week && classItem.start_time) {
      // Recurring class - calculate next occurrence
      const daysOfWeek = {
        'Monday': 1,
        'Tuesday': 2,
        'Wednesday': 3,
        'Thursday': 4,
        'Friday': 5,
        'Saturday': 6,
        'Sunday': 0
      };
      
      const today = new Date();
      const targetDayOfWeek = daysOfWeek[classItem.day_of_week];
      const currentDayOfWeek = today.getDay();
      
      // Calculate days until next occurrence
      let daysUntil = targetDayOfWeek - currentDayOfWeek;
      if (daysUntil < 0) {
        daysUntil += 7; // Next week
      } else if (daysUntil === 0) {
        // Same day - check if time has passed
        const [hours, minutes] = classItem.start_time.split(':').map(Number);
        if (today.getHours() > hours || (today.getHours() === hours && today.getMinutes() >= minutes)) {
          daysUntil = 7; // Next week
        }
      }
      
      // Create target date
      targetDate = new Date(today);
      targetDate.setDate(today.getDate() + daysUntil);
      
      // Set the time from start_time
      const [hours, minutes] = classItem.start_time.split(':').map(Number);
      targetDate.setHours(hours, minutes, 0, 0);
    }
    
    // Populate date fields if we have a target date
    if (targetDate) {
      const year = targetDate.getFullYear().toString();
      const month = (targetDate.getMonth() + 1).toString().padStart(2, '0');
      const day = targetDate.getDate().toString().padStart(2, '0');
      const hour = targetDate.getHours().toString().padStart(2, '0');
      const minute = targetDate.getMinutes().toString().padStart(2, '0');
      
      // Set the date fields
      setDateFields({
        year,
        month,
        day,
        hour,
        minute
      });
      
      // Also set the combined booking_date
      const dateTimeString = `${year}-${month}-${day}T${hour}:${minute}`;
      setBookingForm({
        ...bookingForm,
        class_id: classItem.id,
        booking_date: dateTimeString
      });
    } else {
      setBookingForm({
        ...bookingForm,
        class_id: classItem.id
      });
    }
    
    setShowBookingDialog(true);
  };

  const getClassBookings = (classId) => {
    return bookings.filter(b => b.class_id === classId);
  };

  if (loading) {
    return <div className="flex items-center justify-center h-screen">Loading...</div>;
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">Classes & Scheduling</h1>
        <Dialog open={showClassDialog} onOpenChange={setShowClassDialog}>
          <DialogTrigger asChild>
            <Button onClick={() => { setEditingClass(null); resetClassForm(); }}>
              <Plus className="mr-2 h-4 w-4" /> Add New Class
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{editingClass ? 'Edit Class' : 'Create New Class'}</DialogTitle>
            </DialogHeader>
            <form onSubmit={editingClass ? handleUpdateClass : handleCreateClass} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="name">Class Name *</Label>
                  <Input
                    id="name"
                    value={classForm.name}
                    onChange={(e) => setClassForm({ ...classForm, name: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="class_type">Class Type *</Label>
                  <Select value={classForm.class_type} onValueChange={(value) => setClassForm({ ...classForm, class_type: value })}>
                    <SelectTrigger>
                      <SelectValue placeholder="Select type" />
                    </SelectTrigger>
                    <SelectContent>
                      {CLASS_TYPES.map(type => (
                        <SelectItem key={type} value={type}>{type}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={classForm.description}
                  onChange={(e) => setClassForm({ ...classForm, description: e.target.value })}
                  rows={3}
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="instructor_name">Instructor</Label>
                  <Input
                    id="instructor_name"
                    value={classForm.instructor_name}
                    onChange={(e) => setClassForm({ ...classForm, instructor_name: e.target.value })}
                  />
                </div>
                <div>
                  <Label htmlFor="room">Room/Location</Label>
                  <Input
                    id="room"
                    value={classForm.room}
                    onChange={(e) => setClassForm({ ...classForm, room: e.target.value })}
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label htmlFor="duration_minutes">Duration (min) *</Label>
                  <Input
                    id="duration_minutes"
                    type="number"
                    value={classForm.duration_minutes}
                    onChange={(e) => setClassForm({ ...classForm, duration_minutes: parseInt(e.target.value) })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="capacity">Capacity *</Label>
                  <Input
                    id="capacity"
                    type="number"
                    value={classForm.capacity}
                    onChange={(e) => setClassForm({ ...classForm, capacity: parseInt(e.target.value) })}
                    required
                  />
                </div>
                <div>
                  <Label htmlFor="waitlist_capacity">Waitlist Capacity</Label>
                  <Input
                    id="waitlist_capacity"
                    type="number"
                    value={classForm.waitlist_capacity}
                    onChange={(e) => setClassForm({ ...classForm, waitlist_capacity: parseInt(e.target.value) })}
                  />
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="is_recurring"
                  checked={classForm.is_recurring}
                  onChange={(e) => setClassForm({ ...classForm, is_recurring: e.target.checked })}
                  className="h-4 w-4"
                />
                <Label htmlFor="is_recurring">Recurring Class</Label>
              </div>

              {classForm.is_recurring ? (
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="day_of_week">Day of Week *</Label>
                    <Select value={classForm.day_of_week} onValueChange={(value) => setClassForm({ ...classForm, day_of_week: value })}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select day" />
                      </SelectTrigger>
                      <SelectContent>
                        {DAYS_OF_WEEK.map(day => (
                          <SelectItem key={day} value={day}>{day}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label htmlFor="start_time">Start Time *</Label>
                    <Input
                      id="start_time"
                      type="time"
                      value={classForm.start_time}
                      onChange={(e) => setClassForm({ ...classForm, start_time: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="end_time">End Time *</Label>
                    <Input
                      id="end_time"
                      type="time"
                      value={classForm.end_time}
                      onChange={(e) => setClassForm({ ...classForm, end_time: e.target.value })}
                      required
                    />
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="class_date">Class Date *</Label>
                    <Input
                      id="class_date"
                      type="datetime-local"
                      value={classForm.class_date}
                      onChange={(e) => setClassForm({ ...classForm, class_date: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="start_time">Start Time *</Label>
                    <Input
                      id="start_time"
                      type="time"
                      value={classForm.start_time}
                      onChange={(e) => setClassForm({ ...classForm, start_time: e.target.value })}
                      required
                    />
                  </div>
                  <div>
                    <Label htmlFor="end_time">End Time *</Label>
                    <Input
                      id="end_time"
                      type="time"
                      value={classForm.end_time}
                      onChange={(e) => setClassForm({ ...classForm, end_time: e.target.value })}
                      required
                    />
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="booking_window_days">Booking Window (days)</Label>
                  <Input
                    id="booking_window_days"
                    type="number"
                    value={classForm.booking_window_days}
                    onChange={(e) => setClassForm({ ...classForm, booking_window_days: parseInt(e.target.value) })}
                  />
                </div>
                <div>
                  <Label htmlFor="cancel_window_hours">Cancel Window (hours)</Label>
                  <Input
                    id="cancel_window_hours"
                    type="number"
                    value={classForm.cancel_window_hours}
                    onChange={(e) => setClassForm({ ...classForm, cancel_window_hours: parseInt(e.target.value) })}
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="drop_in_price">Drop-In Price ($)</Label>
                <Input
                  id="drop_in_price"
                  type="number"
                  step="0.01"
                  value={classForm.drop_in_price}
                  onChange={(e) => setClassForm({ ...classForm, drop_in_price: parseFloat(e.target.value) })}
                />
              </div>

              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="allow_waitlist"
                  checked={classForm.allow_waitlist}
                  onChange={(e) => setClassForm({ ...classForm, allow_waitlist: e.target.checked })}
                  className="h-4 w-4"
                />
                <Label htmlFor="allow_waitlist">Allow Waitlist</Label>
              </div>

              <div className="flex justify-end space-x-2">
                <Button type="button" variant="outline" onClick={() => { setShowClassDialog(false); setEditingClass(null); resetClassForm(); }}>
                  Cancel
                </Button>
                <Button type="submit">
                  {editingClass ? 'Update Class' : 'Create Class'}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="schedule">Class Schedule</TabsTrigger>
          <TabsTrigger value="bookings">Bookings</TabsTrigger>
        </TabsList>

        <TabsContent value="schedule" className="space-y-4">
          {DAYS_OF_WEEK.map(day => {
            const dayClasses = classes.filter(c => c.is_recurring && c.day_of_week === day && c.status === 'active');
            if (dayClasses.length === 0) return null;

            return (
              <Card key={day}>
                <CardHeader>
                  <CardTitle className="text-xl">{day}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {dayClasses.map(classItem => {
                      const classBookings = getClassBookings(classItem.id);
                      const confirmedCount = classBookings.filter(b => b.status === 'confirmed').length;
                      const waitlistCount = classBookings.filter(b => b.status === 'waitlist').length;

                      return (
                        <Card key={classItem.id} className="border-l-4 border-l-blue-500">
                          <CardContent className="pt-4">
                            <div className="flex justify-between items-start mb-2">
                              <div>
                                <h4 className="font-semibold text-lg">{classItem.name}</h4>
                                <p className="text-sm text-gray-600">{classItem.class_type}</p>
                              </div>
                              <div className="flex space-x-1">
                                <Button size="sm" variant="ghost" onClick={() => openEditDialog(classItem)}>
                                  <Edit className="h-4 w-4" />
                                </Button>
                                <Button size="sm" variant="ghost" onClick={() => handleDeleteClass(classItem.id)}>
                                  <Trash2 className="h-4 w-4 text-red-500" />
                                </Button>
                              </div>
                            </div>

                            <div className="space-y-1 text-sm text-gray-600 mb-3">
                              <div className="flex items-center">
                                <Clock className="h-4 w-4 mr-2" />
                                {classItem.start_time} - {classItem.end_time}
                              </div>
                              {classItem.instructor_name && (
                                <div className="flex items-center">
                                  <UserCheck className="h-4 w-4 mr-2" />
                                  {classItem.instructor_name}
                                </div>
                              )}
                              <div className="flex items-center">
                                <Users className="h-4 w-4 mr-2" />
                                {confirmedCount}/{classItem.capacity} booked
                                {waitlistCount > 0 && ` (+${waitlistCount} waitlist)`}
                              </div>
                            </div>

                            <Button
                              size="sm"
                              className="w-full"
                              onClick={() => openBookingDialog(classItem)}
                            >
                              <Plus className="h-4 w-4 mr-2" /> Book Member
                            </Button>
                          </CardContent>
                        </Card>
                      );
                    })}
                  </div>
                </CardContent>
              </Card>
            );
          })}

          {classes.filter(c => c.is_recurring && c.status === 'active').length === 0 && (
            <Card>
              <CardContent className="text-center py-12">
                <Calendar className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                <p className="text-gray-600">No classes scheduled yet. Create your first class to get started!</p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="bookings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>All Bookings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b">
                      <th className="text-left p-2">Member</th>
                      <th className="text-left p-2">Class</th>
                      <th className="text-left p-2">Date/Time</th>
                      <th className="text-left p-2">Status</th>
                      <th className="text-left p-2">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {bookings.map(booking => (
                      <tr key={booking.id} className="border-b hover:bg-gray-50">
                        <td className="p-2">{booking.member_name}</td>
                        <td className="p-2">{booking.class_name}</td>
                        <td className="p-2">
                          {new Date(booking.booking_date).toLocaleString()}
                        </td>
                        <td className="p-2">
                          <span className={`px-2 py-1 rounded text-xs ${
                            booking.status === 'confirmed' ? 'bg-green-100 text-green-800' :
                            booking.status === 'waitlist' ? 'bg-yellow-100 text-yellow-800' :
                            booking.status === 'attended' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {booking.status}
                            {booking.is_waitlist && ` (#${booking.waitlist_position})`}
                          </span>
                        </td>
                        <td className="p-2">
                          <div className="flex space-x-2">
                            {booking.status === 'confirmed' && (
                              <Button size="sm" onClick={() => handleCheckIn(booking.id)}>
                                Check In
                              </Button>
                            )}
                            {['confirmed', 'waitlist'].includes(booking.status) && (
                              <Button
                                size="sm"
                                variant="destructive"
                                onClick={() => handleCancelBooking(booking.id)}
                              >
                                Cancel
                              </Button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {bookings.length === 0 && (
                  <div className="text-center py-12">
                    <p className="text-gray-600">No bookings yet</p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <Dialog open={showBookingDialog} onOpenChange={setShowBookingDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create Booking</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateBooking} className="space-y-4">
            <div>
              <Label>Class</Label>
              <Input value={selectedClass?.name || ''} disabled />
            </div>

            <div>
              <Label htmlFor="member_id">Member *</Label>
              <Popover open={memberSearchOpen} onOpenChange={setMemberSearchOpen}>
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    role="combobox"
                    aria-expanded={memberSearchOpen}
                    className="w-full justify-between"
                  >
                    {bookingForm.member_id
                      ? (() => {
                          const member = members.find((m) => m.id === bookingForm.member_id);
                          return member ? `${member.first_name} ${member.last_name}` : "Select member...";
                        })()
                      : "Select member..."}
                    <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-full p-0">
                  <Command>
                    <CommandInput 
                      placeholder="Search member by name..." 
                    />
                    <CommandList>
                      <CommandEmpty>No member found.</CommandEmpty>
                      <CommandGroup>
                        {members.map((member) => (
                          <CommandItem
                            key={member.id}
                            value={`${member.first_name} ${member.last_name}`}
                            onSelect={() => {
                              setBookingForm({ ...bookingForm, member_id: member.id });
                              setMemberSearchOpen(false);
                            }}
                          >
                            <Check
                              className={`mr-2 h-4 w-4 ${
                                bookingForm.member_id === member.id ? "opacity-100" : "opacity-0"
                              }`}
                            />
                            {member.first_name} {member.last_name}
                            {member.membership_number && (
                              <span className="ml-2 text-xs text-gray-500">
                                #{member.membership_number}
                              </span>
                            )}
                          </CommandItem>
                        ))}
                      </CommandGroup>
                    </CommandList>
                  </Command>
                </PopoverContent>
              </Popover>
            </div>

            <div>
              <Label>Date & Time *</Label>
              <div className="flex gap-2 items-center">
                <div className="flex-1">
                  <Input
                    ref={yearRef}
                    type="text"
                    placeholder="YYYY"
                    value={dateFields.year}
                    onChange={(e) => handleDateFieldChange('year', e.target.value, 4, monthRef)}
                    maxLength={4}
                    className="text-center"
                  />
                </div>
                <span className="text-gray-500">/</span>
                <div className="flex-1">
                  <Input
                    ref={monthRef}
                    type="text"
                    placeholder="MM"
                    value={dateFields.month}
                    onChange={(e) => handleDateFieldChange('month', e.target.value, 2, dayRef)}
                    maxLength={2}
                    className="text-center"
                  />
                </div>
                <span className="text-gray-500">/</span>
                <div className="flex-1">
                  <Input
                    ref={dayRef}
                    type="text"
                    placeholder="DD"
                    value={dateFields.day}
                    onChange={(e) => handleDateFieldChange('day', e.target.value, 2, hourRef)}
                    maxLength={2}
                    className="text-center"
                  />
                </div>
                <span className="text-gray-500 mx-2">at</span>
                <div className="flex-1">
                  <Input
                    ref={hourRef}
                    type="text"
                    placeholder="HH"
                    value={dateFields.hour}
                    onChange={(e) => handleDateFieldChange('hour', e.target.value, 2, minuteRef)}
                    maxLength={2}
                    className="text-center"
                  />
                </div>
                <span className="text-gray-500">:</span>
                <div className="flex-1">
                  <Input
                    ref={minuteRef}
                    type="text"
                    placeholder="MM"
                    value={dateFields.minute}
                    onChange={(e) => handleDateFieldChange('minute', e.target.value, 2, null)}
                    maxLength={2}
                    className="text-center"
                  />
                </div>
              </div>
              <p className="text-xs text-gray-500 mt-1">Format: YYYY/MM/DD at HH:MM (24-hour)</p>
            </div>

            <div>
              <Label htmlFor="notes">Notes</Label>
              <Textarea
                id="notes"
                value={bookingForm.notes}
                onChange={(e) => setBookingForm({ ...bookingForm, notes: e.target.value })}
                rows={3}
              />
            </div>

            <div className="flex justify-end space-x-2">
              <Button type="button" variant="outline" onClick={() => { setShowBookingDialog(false); resetBookingForm(); }}>
                Cancel
              </Button>
              <Button type="submit">Create Booking</Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default Classes;
