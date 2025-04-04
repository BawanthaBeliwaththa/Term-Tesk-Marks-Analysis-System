$(document).ready(function(){
    // Add Marks Handler
    $('#addMarks').click(function(){
        $('#marksModal').modal('show');
        $('#marksForm')[0].reset();
        $('.modal-title').html("<i class='fa fa-plus'></i> Add Test Marks");
        $('#action').val('addMarks');
        $('#save').val('Save Marks');
    });

    // Edit Marks Handler (if needed)
    $('.editMarks').click(function(){
        $('#marksModal').modal('show');
        $('.modal-title').html("<i class='fa fa-edit'></i> Edit Test Marks");
        $('#action').val('updateMarks');
        $('#save').val('Update Marks');
    });
});